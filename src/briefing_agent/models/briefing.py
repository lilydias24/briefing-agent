from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    """Represents a single news article."""

    title: str
    summary: str
    url: str
    source: str


@dataclass
class TopicBriefing:
    """Represents the briefing for a single topic."""

    topic: str
    articles: list[Article] = field(default_factory=list)


@dataclass
class Briefing:
    """Represents the full consolidated briefing to be sent."""

    topics: list[TopicBriefing] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)