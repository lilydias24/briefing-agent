import json
import os

from briefing_agent.models.briefing import Briefing
from briefing_agent.models.preferences import UserPreferences, TopicPreference
from briefing_agent.storage.base import BaseStorage


class JsonStorage(BaseStorage):
    """Persistence layer using JSON files."""

    def __init__(self, prefs_file: str = "preferences.json", briefings_file: str = "briefings.json") -> None:
        """Initialize with file paths."""
        self._prefs_file = prefs_file
        self._briefings_file = briefings_file

    def save(self, preferences: UserPreferences) -> None:
        """Persist user preferences to JSON."""
        data = {
            "email": preferences.email,
            "discord_channel_id": preferences.discord_channel_id,
            "schedule_hour": preferences.schedule_hour,
            "schedule_minute": preferences.schedule_minute,
            "topics": [
                {
                    "name": t.name,
                    "keywords": t.keywords,
                    "max_articles": t.max_articles,
                }
                for t in preferences.topics
            ],
        }
        with open(self._prefs_file, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> UserPreferences | None:
        """Load user preferences from JSON."""
        if not os.path.exists(self._prefs_file):
            return None

        with open(self._prefs_file, "r") as f:
            data = json.load(f)

        topics = [
            TopicPreference(
                name=t["name"],
                keywords=t["keywords"],
                max_articles=t["max_articles"],
            )
            for t in data.get("topics", [])
        ]

        return UserPreferences(
            email=data["email"],
            discord_channel_id=data["discord_channel_id"],
            topics=topics,
            schedule_hour=data.get("schedule_hour", 7),
            schedule_minute=data.get("schedule_minute", 0),
        )

    def save_briefing(self, briefing: Briefing) -> None:
        """Save briefing to JSON with timestamp."""
        briefings = []
        if os.path.exists(self._briefings_file):
            with open(self._briefings_file, "r") as f:
                briefings = json.load(f)

        new_briefing = {
            "generated_at": briefing.generated_at.isoformat(),
            "topics": [
                {
                    "topic": t.topic,
                    "articles": [
                        {
                            "title": a.title,
                            "summary": a.summary,
                            "url": a.url,
                            "source": a.source,
                        }
                        for a in t.articles
                    ],
                }
                for t in briefing.topics
            ],
        }
        briefings.append(new_briefing)

        with open(self._briefings_file, "w") as f:
            json.dump(briefings[-30:], f, indent=2)

        print(f"✅ Briefing saved to {self._briefings_file}")