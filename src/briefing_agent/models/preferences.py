# Aqui a gente vai definir o que o usuário configura no Discord.


from dataclasses import dataclass, field


@dataclass
class TopicPreference:
    """Represents a topic of interest with associated keywords and limits."""

    name: str
    keywords: list[str]
    max_articles: int


@dataclass
class UserPreferences:
    """Represents the full set of preferences configured by the user."""

    topics: list[TopicPreference] = field(default_factory=list)
    email: str = ""
    discord_channel_id: str = ""