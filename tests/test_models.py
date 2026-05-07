from __future__ import annotations

from datetime import datetime

import pytest

from briefing_agent.models.briefing import Article, Briefing, TopicBriefing
from briefing_agent.models.preferences import TopicPreference, UserPreferences


class TestArticle:
    """Tests for the Article dataclass."""

    def test_basic_instantiation(self) -> None:
        """All four fields are stored and retrievable after construction."""
        article = Article(
            title="Title", summary="Summary", url="https://a.com", source="Source"
        )
        assert article.title == "Title"
        assert article.summary == "Summary"
        assert article.url == "https://a.com"
        assert article.source == "Source"

    def test_empty_strings(self) -> None:
        """Article accepts empty strings for every field without raising."""
        article = Article(title="", summary="", url="", source="")
        assert article.title == ""
        assert article.summary == ""
        assert article.url == ""
        assert article.source == ""

    def test_long_strings(self) -> None:
        """Article stores arbitrarily long strings without truncation."""
        long_str = "x" * 10_000
        article = Article(title=long_str, summary=long_str, url=long_str, source=long_str)
        assert len(article.title) == 10_000
        assert len(article.summary) == 10_000

    def test_special_characters(self) -> None:
        """Article preserves special characters such as HTML entities and accents."""
        article = Article(
            title="Título: \"cotações\" & análise",
            summary="Resumo com <html> e & símbolos",
            url="https://example.com/path?q=1&lang=pt",
            source="O Globo",
        )
        assert "<html>" in article.summary
        assert "cotações" in article.title

    def test_equality(self) -> None:
        """Two Article instances with identical fields are equal."""
        a1 = Article(title="T", summary="S", url="https://a.com", source="X")
        a2 = Article(title="T", summary="S", url="https://a.com", source="X")
        assert a1 == a2

    def test_inequality_on_different_url(self) -> None:
        """Two Article instances that differ only in URL are not equal."""
        a1 = Article(title="T", summary="S", url="https://a.com", source="X")
        a2 = Article(title="T", summary="S", url="https://b.com", source="X")
        assert a1 != a2


class TestTopicBriefing:
    """Tests for the TopicBriefing dataclass."""

    def test_default_articles_is_empty_list(self) -> None:
        """articles defaults to an empty list when not provided."""
        tb = TopicBriefing(topic="tech")
        assert tb.articles == []

    def test_articles_list_is_independent_per_instance(self) -> None:
        """Mutating one instance's articles list does not affect another instance."""
        tb1 = TopicBriefing(topic="tech")
        tb2 = TopicBriefing(topic="energy")
        tb1.articles.append(
            Article(title="T", summary="S", url="https://a.com", source="X")
        )
        assert tb2.articles == []

    def test_with_articles(self, sample_article: Article) -> None:
        """Articles passed at construction are accessible via the articles field."""
        tb = TopicBriefing(topic="tech", articles=[sample_article])
        assert len(tb.articles) == 1
        assert tb.articles[0] == sample_article

    def test_topic_name_preserved(self) -> None:
        """The topic name is stored exactly as given."""
        tb = TopicBriefing(topic="cybersecurity")
        assert tb.topic == "cybersecurity"


class TestBriefing:
    """Tests for the Briefing dataclass."""

    def test_generated_at_is_datetime(self) -> None:
        """generated_at is automatically set to a datetime instance."""
        briefing = Briefing()
        assert isinstance(briefing.generated_at, datetime)

    def test_generated_at_is_close_to_now(self) -> None:
        """generated_at falls between the timestamps taken just before and after construction."""
        before = datetime.now()
        briefing = Briefing()
        after = datetime.now()
        assert before <= briefing.generated_at <= after

    def test_two_briefings_have_non_decreasing_timestamps(self) -> None:
        """A briefing created later has a timestamp >= the one created earlier."""
        b1 = Briefing()
        b2 = Briefing()
        assert b1.generated_at <= b2.generated_at

    def test_default_topics_is_empty_list(self) -> None:
        """topics defaults to an empty list when not provided."""
        briefing = Briefing()
        assert briefing.topics == []

    def test_topics_list_is_independent_per_instance(self) -> None:
        """Mutating one instance's topics list does not affect another instance."""
        b1 = Briefing()
        b2 = Briefing()
        b1.topics.append(TopicBriefing(topic="tech"))
        assert b2.topics == []

    def test_with_topic_briefings(self, sample_briefing: Briefing) -> None:
        """Briefing built with topic briefings exposes them via the topics field."""
        assert len(sample_briefing.topics) == 1
        assert sample_briefing.topics[0].topic == "technology"

    def test_custom_generated_at(self) -> None:
        """generated_at can be overridden at construction time."""
        custom_dt = datetime(2024, 1, 15, 7, 0, 0)
        briefing = Briefing(generated_at=custom_dt)
        assert briefing.generated_at == custom_dt


class TestTopicPreference:
    """Tests for the TopicPreference dataclass."""

    def test_defaults(self) -> None:
        """keywords defaults to [] and max_articles defaults to 5."""
        tp = TopicPreference(name="energy")
        assert tp.keywords == []
        assert tp.max_articles == 5

    def test_empty_keywords_list(self) -> None:
        """Explicitly passing an empty keywords list is accepted."""
        tp = TopicPreference(name="energy", keywords=[])
        assert tp.keywords == []

    def test_zero_max_articles(self) -> None:
        """max_articles accepts zero without raising."""
        tp = TopicPreference(name="energy", max_articles=0)
        assert tp.max_articles == 0

    def test_negative_max_articles(self) -> None:
        """max_articles accepts negative values without raising."""
        tp = TopicPreference(name="energy", max_articles=-3)
        assert tp.max_articles == -3

    def test_large_max_articles(self) -> None:
        """max_articles accepts large values without raising."""
        tp = TopicPreference(name="energy", max_articles=1000)
        assert tp.max_articles == 1000

    def test_keywords_list_is_independent_per_instance(self) -> None:
        """Mutating one instance's keywords list does not affect another instance."""
        tp1 = TopicPreference(name="a")
        tp2 = TopicPreference(name="b")
        tp1.keywords.append("AI")
        assert tp2.keywords == []

    def test_name_preserved(self) -> None:
        """The topic name is stored exactly as given, including spaces."""
        tp = TopicPreference(name="smart grid")
        assert tp.name == "smart grid"

    def test_multiple_keywords(self) -> None:
        """Multiple keywords are stored and accessible in their original order."""
        tp = TopicPreference(name="tech", keywords=["AI", "ML", "LLM"])
        assert len(tp.keywords) == 3
        assert "ML" in tp.keywords


class TestUserPreferences:
    """Tests for the UserPreferences dataclass."""

    def test_defaults(self) -> None:
        """All fields have expected default values when not provided."""
        prefs = UserPreferences()
        assert prefs.topics == []
        assert prefs.email == ""
        assert prefs.discord_channel_id == ""
        assert prefs.schedule_hour == 7
        assert prefs.schedule_minute == 0

    def test_empty_email_is_valid(self) -> None:
        """An empty string is a valid value for the email field."""
        prefs = UserPreferences(email="")
        assert prefs.email == ""

    def test_no_topics(self) -> None:
        """An empty topics list is accepted without raising."""
        prefs = UserPreferences(topics=[])
        assert prefs.topics == []

    def test_topics_list_is_independent_per_instance(self) -> None:
        """Mutating one instance's topics list does not affect another instance."""
        p1 = UserPreferences()
        p2 = UserPreferences()
        p1.topics.append(TopicPreference(name="tech"))
        assert p2.topics == []

    def test_schedule_hour_boundary_zero(self) -> None:
        """schedule_hour of 0 is accepted (midnight)."""
        prefs = UserPreferences(schedule_hour=0, schedule_minute=0)
        assert prefs.schedule_hour == 0

    def test_schedule_hour_boundary_max(self) -> None:
        """schedule_hour of 23 and schedule_minute of 59 are accepted."""
        prefs = UserPreferences(schedule_hour=23, schedule_minute=59)
        assert prefs.schedule_hour == 23
        assert prefs.schedule_minute == 59

    def test_multiple_topics(self) -> None:
        """Multiple topics are stored in order."""
        topics = [TopicPreference(name="tech"), TopicPreference(name="energy")]
        prefs = UserPreferences(topics=topics)
        assert len(prefs.topics) == 2
        assert prefs.topics[0].name == "tech"

    def test_full_construction(self) -> None:
        """All fields are stored correctly when all are provided at construction."""
        prefs = UserPreferences(
            topics=[TopicPreference(name="tech", keywords=["AI"], max_articles=3)],
            email="user@example.com",
            discord_channel_id="123456",
            schedule_hour=8,
            schedule_minute=30,
        )
        assert prefs.email == "user@example.com"
        assert prefs.discord_channel_id == "123456"
        assert prefs.schedule_hour == 8
        assert prefs.schedule_minute == 30
