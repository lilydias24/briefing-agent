from dataclasses import dataclass, field


@dataclass
class TopicPreference:
    """Represents a topic configured by the user."""

    name: str
    keywords: list[str] = field(default_factory=list)
    max_articles: int = 5


@dataclass
class UserPreferences:
    """Represents all preferences configured by the user."""

    topics: list[TopicPreference] = field(default_factory=list)
    email: str = ""
    discord_channel_id: str = ""