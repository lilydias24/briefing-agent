from __future__ import annotations

import re
from dataclasses import dataclass, field

from briefing_agent.agents.base import BaseAgent
from briefing_agent.models.preferences import TopicPreference, UserPreferences
from briefing_agent.storage.base import BaseStorage

# --- Constants for Messages and Prompts ---
RESET_COMMANDS = {"reset", "restart", "cancel"}

ERR_NO_TOPICS = "Please provide at least one topic. Example: technology, energy, cybersecurity"
ERR_INVALID_EMAIL = "Could not identify a valid email. Example: user@example.com"
ERR_NOT_A_NUMBER = "Please provide a positive integer. Example: 5"
ERR_NUMBER_TOO_SMALL = "The maximum number of articles must be greater than zero."

QUESTIONS = {
    1: "Which topics do you want to follow? Separate by comma. Example: energy, cybersecurity",
    2: "Which keywords should I use? Separate by comma. Example: smart grid, IEC 61850, ransomware",
    3: "What is the maximum number of articles per topic? Example: 5",
    4: "Which email should receive the briefing?",
    5: "What is the Discord channel ID that should receive the briefing?",
    6: "What time should the briefing be sent? Format: HH:MM (e.g., 14:30)",
}

CONFIRMATION_TEMPLATE = (
    "Preferences saved successfully.\n"
    "Topics: {topics}\n"
    "Email: {email}\n"
    "Discord Channel: {discord}\n"
    "Briefing Time: {schedule_time}"
)

@dataclass
class _SetupSession:
    """Temporary in-memory state while a user is configuring preferences."""

    step: int = 0
    topics: list[str] = field(default_factory=list)
    keywords_by_topic: dict[str, list[str]] = field(default_factory=dict)
    max_articles: int = 5
    email: str = ""
    discord_channel_id: str = ""
    schedule_hour: int = 7
    schedule_minute: int = 0


class SetupAgent(BaseAgent):
    """Collects and persists user preferences via a step-by-step chat flow."""

    def __init__(self, storage: BaseStorage) -> None:
        """Initialize with a storage dependency for saving preferences."""
        self._storage = storage
        self._sessions: dict[str, _SetupSession] = {}
        self._scheduler = None

    def attach_scheduler(self, scheduler) -> None:
        """Attach a running scheduler so the setup agent can request reschedules."""
        self._scheduler = scheduler


    def run(self, user_message: str, session_id: str = "default") -> str:
        """Process a user message, update the setup state, and persist when complete.

        Parameters
        ----------
        user_message:
            Message sent by the user in Discord.
        session_id:
            Identifier used to isolate simultaneous setup conversations. In Discord,
            this should usually be the author ID.
        """
        session = self._sessions.setdefault(session_id, _SetupSession())
        message = user_message.strip()

        if not message:
            current_step = session.step if session.step > 0 else 1
            return self._question_for_step(current_step)

        if message.lower() in RESET_COMMANDS:
            self._sessions[session_id] = _SetupSession(step=1)
            return self._question_for_step(1)

        try:
            if session.step == 0:
                session.step = 1
                return self._question_for_step(1)
            
            if session.step == 1:
                session.topics = self._parse_csv(message)
                if not session.topics:
                    return ERR_NO_TOPICS
                session.step = 2
                return self._question_for_step(2)

            if session.step == 2:
                session.keywords_by_topic = self._parse_keywords(message, session.topics)
                session.step = 3
                return self._question_for_step(3)

            if session.step == 3:
                session.max_articles = self._parse_positive_int(message)
                session.step = 4
                return self._question_for_step(4)

            if session.step == 4:
                email = self._extract_email(message)
                if not email:
                    return ERR_INVALID_EMAIL
                session.email = email
                session.step = 5
                return self._question_for_step(5)

            if session.step == 5:
                session.discord_channel_id = message
                session.step = 6
                return self._question_for_step(6)

            if session.step == 6:
                hour, minute = self._parse_time(message)
                session.schedule_hour = hour
                session.schedule_minute = minute
                preferences = self._build_preferences(session)
                self.save_preferences(preferences)
                del self._sessions[session_id]
                return self._confirmation(preferences)

        except ValueError as exc:
            return str(exc)

        return self._question_for_step(session.step)

    def save_preferences(self, preferences: UserPreferences) -> None:
        """Persist the collected user preferences."""
        self._storage.save(preferences)
        # If a scheduler is attached, request a reschedule so new time takes effect immediately
        try:
            if self._scheduler is not None:
                self._scheduler.reschedule()
                print("[setup] Scheduler notified of updated preferences.")
        except Exception:
            # Keep setup flow resilient; don't crash on scheduler errors
            print("[setup] Failed to notify scheduler about preference changes.")

    def _build_preferences(self, session: _SetupSession) -> UserPreferences:
        topics = [
            TopicPreference(
                name=topic,
                keywords=session.keywords_by_topic.get(topic, []),
                max_articles=session.max_articles,
            )
            for topic in session.topics
        ]
        return UserPreferences(
            topics=topics,
            email=session.email,
            discord_channel_id=session.discord_channel_id,
            schedule_hour=session.schedule_hour,
            schedule_minute=session.schedule_minute,
        )

    def _question_for_step(self, step: int) -> str:
        return QUESTIONS.get(step, QUESTIONS[1])

    def _confirmation(self, preferences: UserPreferences) -> str:
        topic_names = ", ".join(topic.name for topic in preferences.topics)
        schedule_time = f"{preferences.schedule_hour:02d}:{preferences.schedule_minute:02d}"
        confirmation = CONFIRMATION_TEMPLATE.format(
            topics=topic_names, 
            email=preferences.email, 
            discord=preferences.discord_channel_id,
            schedule_time=schedule_time
        )
        print(f"\n✅ [SETUP COMPLETED] All preferences received and saved successfully!")
        return confirmation

    def _parse_csv(self, value: str) -> list[str]:
        return [item.strip() for item in value.split(",") if item.strip()]

    def _parse_keywords(self, value: str, topics: list[str]) -> dict[str, list[str]]:
        """Parse keywords globally or by topic.

        Supported formats:
        - "smart grid, IEC 61850" -> same keywords for all topics
        - "energia: solar, eólica; segurança: ransomware, IDS" -> per topic
        """
        if ":" not in value:
            keywords = self._parse_csv(value)
            return {topic: keywords for topic in topics}

        normalized_topics = {topic.lower(): topic for topic in topics}
        keywords_by_topic = {topic: [] for topic in topics}

        for block in value.split(";"):
            if ":" not in block:
                continue
            topic_name, raw_keywords = block.split(":", 1)
            canonical_topic = normalized_topics.get(topic_name.strip().lower())
            if canonical_topic:
                keywords_by_topic[canonical_topic] = self._parse_csv(raw_keywords)

        # If the user used a per-topic format but missed some topics, keep them empty.
        return keywords_by_topic

    def _parse_positive_int(self, value: str) -> int:
        match = re.search(r"\d+", value)
        if not match:
            raise ValueError(ERR_NOT_A_NUMBER)
        number = int(match.group(0))
        if number <= 0:
            raise ValueError(ERR_NUMBER_TOO_SMALL)
        return number

    def _extract_email(self, value: str) -> str:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", value)
        return match.group(0) if match else ""

    def _parse_time(self, value: str) -> tuple[int, int]:
        """Parse time in HH:MM format.
        
        Returns
        -------
        tuple[int, int]
            A tuple of (hour, minute).

        Raises
        ------
        ValueError
            If the format is invalid or values are out of range.
        """
        match = re.search(r"(\d{1,2}):(\d{2})", value)
        if not match:
            raise ValueError("Please provide time in HH:MM format. Example: 14:30")
        
        hour = int(match.group(1))
        minute = int(match.group(2))
        
        if not (0 <= hour <= 23):
            raise ValueError("Hour must be between 0 and 23.")
        if not (0 <= minute <= 59):
            raise ValueError("Minute must be between 0 and 59.")
        
        return hour, minute