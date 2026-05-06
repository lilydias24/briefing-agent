from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from briefing_agent.models.briefing import Article, Briefing, TopicBriefing
from briefing_agent.models.preferences import TopicPreference, UserPreferences


@pytest.fixture
def sample_article() -> Article:
    """Return a reusable sample article for tests."""
    return Article(
        title="Sample title",
        summary="Sample summary",
        url="https://example.com/article",
        source="Example News",
    )


@pytest.fixture
def sample_preferences() -> UserPreferences:
    """Return reusable user preferences for tests."""
    return UserPreferences(
        topics=[
            TopicPreference(
                name="technology",
                keywords=["AI", "software"],
                max_articles=2,
            )
        ],
        email="user@example.com",
        discord_channel_id="123456789",
    )


@pytest.fixture
def sample_briefing(sample_article: Article) -> Briefing:
    """Return a reusable briefing for tests."""
    return Briefing(
        topics=[
            TopicBriefing(
                topic="technology",
                articles=[sample_article],
            )
        ]
    )


@dataclass
class FakeStorage:
    """In-memory storage double used by tests."""

    preferences: UserPreferences | None = None
    briefings: list[Briefing] = field(default_factory=list)

    def save(self, preferences: UserPreferences) -> None:
        """Save preferences in memory."""
        self.preferences = preferences

    def load(self) -> UserPreferences | None:
        """Load preferences from memory."""
        return self.preferences

    def save_briefing(self, briefing: Briefing) -> None:
        """Save a briefing in memory."""
        self.briefings.append(briefing)


@pytest.fixture
def fake_storage(sample_preferences: UserPreferences) -> FakeStorage:
    """Return an in-memory storage instance with sample preferences."""
    return FakeStorage(preferences=sample_preferences)


class FakeNewsFetcher:
    """News fetcher double used by tests."""

    def __init__(self, articles: list[Article]) -> None:
        """Initialize with the articles that should be returned."""
        self.articles = articles
        self.calls: list[dict[str, Any]] = []

    def run(self, topic: str, keywords: list[str], max_articles: int) -> list[Article]:
        """Record the call and return predefined articles."""
        self.calls.append(
            {
                "topic": topic,
                "keywords": keywords,
                "max_articles": max_articles,
            }
        )
        return self.articles


@pytest.fixture
def fake_news_fetcher(sample_article: Article) -> FakeNewsFetcher:
    """Return a news fetcher double with one sample article."""
    return FakeNewsFetcher([sample_article])


class FakeSender:
    """Sender double used for email and Discord tests."""

    def __init__(self) -> None:
        """Initialize an empty call list."""
        self.calls: list[tuple[Any, ...]] = []

    def run(self, *args: Any) -> None:
        """Record arguments passed to the sender."""
        self.calls.append(args)


@pytest.fixture
def fake_email_sender() -> FakeSender:
    """Return an email sender double."""
    return FakeSender()


@pytest.fixture
def fake_discord_sender() -> FakeSender:
    """Return a Discord sender double."""
    return FakeSender()