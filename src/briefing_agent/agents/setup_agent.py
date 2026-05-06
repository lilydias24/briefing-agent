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
}

CONFIRMATION_TEMPLATE = (
    "Preferences saved successfully.\n"
    "Topics: {topics}\n"
    "Email: {email}\n"
    "Discord Channel: {discord}"
)

@dataclass
class _SetupSession:
    """Temporary in-memory state while a user is configuring preferences."""

    step: int = 1
    topics: list[str] = field(default_factory=list)
    keywords_by_topic: dict[str, list[str]] = field(default_factory=dict)
    max_articles: int = 5
    email: str = ""
    discord_channel_id: str = ""


class SetupAgent(BaseAgent):
    """Collects and persists user preferences via a step-by-step chat flow."""

    def __init__(self, storage: BaseStorage) -> None:
        """Initialize with a storage dependency for saving preferences."""
        self._storage = storage
        self._sessions: dict[str, _SetupSession] = {}

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
            return self._question_for_step(session.step)

        if message.lower() in RESET_COMMANDS:
            self._sessions[session_id] = _SetupSession()
            return self._question_for_step(1)

        try:
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
        )

    def _question_for_step(self, step: int) -> str:
        return QUESTIONS.get(step, QUESTIONS[1])

    def _confirmation(self, preferences: UserPreferences) -> str:
        topic_names = ", ".join(topic.name for topic in preferences.topics)
        return CONFIRMATION_TEMPLATE.format(
            topics=topic_names, 
            email=preferences.email, 
            discord=preferences.discord_channel_id
        )

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