from __future__ import annotations

import json
from pathlib import Path

import pytest

from briefing_agent.models.briefing import Article, Briefing, TopicBriefing
from briefing_agent.models.preferences import TopicPreference, UserPreferences
from briefing_agent.storage.json_storage import JsonStorage


# ---------------------------------------------------------------------------
# Helpers / factories
# ---------------------------------------------------------------------------

def _make_storage(tmp_path: Path) -> JsonStorage:
    """Return a JsonStorage instance writing to isolated temporary files."""
    return JsonStorage(
        prefs_file=str(tmp_path / "prefs.json"),
        briefings_file=str(tmp_path / "briefings.json"),
    )


def _sample_preferences() -> UserPreferences:
    """Return a fully populated UserPreferences instance for round-trip tests."""
    return UserPreferences(
        topics=[
            TopicPreference(name="technology", keywords=["AI", "ML"], max_articles=3),
            TopicPreference(name="energy", keywords=["solar"], max_articles=5),
        ],
        email="user@example.com",
        discord_channel_id="123456789",
        schedule_hour=8,
        schedule_minute=30,
    )


def _make_briefing(title: str = "Article") -> Briefing:
    """Return a minimal Briefing instance for save_briefing tests."""
    article = Article(title=title, summary="Summary", url="https://a.com", source="Src")
    return Briefing(topics=[TopicBriefing(topic="tech", articles=[article])])


# ---------------------------------------------------------------------------
# load() — non-existent file
# ---------------------------------------------------------------------------

class TestLoadNonExistentFile:
    """Tests for JsonStorage.load() when the preferences file does not exist."""

    def test_returns_none_when_file_missing(self, tmp_path: Path) -> None:
        """load() returns None without raising when the preferences file is absent."""
        storage = _make_storage(tmp_path)
        result = storage.load()
        assert result is None

    def test_does_not_raise_when_file_missing(self, tmp_path: Path) -> None:
        """load() completes without any exception when the preferences file is absent."""
        storage = _make_storage(tmp_path)
        try:
            storage.load()
        except Exception as exc:
            pytest.fail(f"load() raised an unexpected exception: {exc}")

    def test_missing_briefings_file_does_not_affect_load(self, tmp_path: Path) -> None:
        """Absence of the briefings file has no effect on load() for preferences."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        result = storage.load()
        assert result is not None


# ---------------------------------------------------------------------------
# save() / load() round-trip
# ---------------------------------------------------------------------------

class TestRoundTrip:
    """Tests verifying that save() followed by load() reproduces the original data."""

    def test_email_is_preserved(self, tmp_path: Path) -> None:
        """The email field survives a full save→load round-trip."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        assert loaded.email == "user@example.com"

    def test_discord_channel_id_is_preserved(self, tmp_path: Path) -> None:
        """The discord_channel_id field survives a full save→load round-trip."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        assert loaded.discord_channel_id == "123456789"

    def test_schedule_hour_is_preserved(self, tmp_path: Path) -> None:
        """The schedule_hour field survives a full save→load round-trip."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        assert loaded.schedule_hour == 8

    def test_schedule_minute_is_preserved(self, tmp_path: Path) -> None:
        """The schedule_minute field survives a full save→load round-trip."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        assert loaded.schedule_minute == 30

    def test_topic_count_is_preserved(self, tmp_path: Path) -> None:
        """The number of topics survives a full save→load round-trip."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        assert len(loaded.topics) == 2

    def test_topic_name_is_preserved(self, tmp_path: Path) -> None:
        """Each topic name survives a full save→load round-trip."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        names = [t.name for t in loaded.topics]
        assert "technology" in names
        assert "energy" in names

    def test_topic_keywords_are_preserved(self, tmp_path: Path) -> None:
        """Each topic's keyword list survives a full save→load round-trip."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        tech = next(t for t in loaded.topics if t.name == "technology")
        assert tech.keywords == ["AI", "ML"]

    def test_topic_max_articles_is_preserved(self, tmp_path: Path) -> None:
        """Each topic's max_articles value survives a full save→load round-trip."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        tech = next(t for t in loaded.topics if t.name == "technology")
        assert tech.max_articles == 3

    def test_empty_topics_list_is_preserved(self, tmp_path: Path) -> None:
        """An empty topics list survives a full save→load round-trip."""
        storage = _make_storage(tmp_path)
        prefs = UserPreferences(email="a@b.com", discord_channel_id="1")
        storage.save(prefs)
        loaded = storage.load()
        assert loaded.topics == []

    def test_overwrite_replaces_previous_preferences(self, tmp_path: Path) -> None:
        """A second save() overwrites the first; only the latest values are returned by load()."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        updated = UserPreferences(
            topics=[],
            email="new@example.com",
            discord_channel_id="999",
            schedule_hour=14,
            schedule_minute=0,
        )
        storage.save(updated)
        loaded = storage.load()
        assert loaded.email == "new@example.com"
        assert loaded.discord_channel_id == "999"

    def test_loaded_object_is_user_preferences_instance(self, tmp_path: Path) -> None:
        """load() returns a UserPreferences instance, not a raw dict."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        assert isinstance(loaded, UserPreferences)

    def test_loaded_topics_are_topic_preference_instances(self, tmp_path: Path) -> None:
        """Each topic in the loaded preferences is a TopicPreference instance."""
        storage = _make_storage(tmp_path)
        storage.save(_sample_preferences())
        loaded = storage.load()
        assert all(isinstance(t, TopicPreference) for t in loaded.topics)


# ---------------------------------------------------------------------------
# save_briefing() — accumulation and 30-item limit
# ---------------------------------------------------------------------------

class TestSaveBriefing:
    """Tests for JsonStorage.save_briefing() including the 30-briefing retention limit."""

    def test_first_briefing_is_saved(self, tmp_path: Path) -> None:
        """After one save_briefing call, the briefings file contains exactly one entry."""
        storage = _make_storage(tmp_path)
        storage.save_briefing(_make_briefing())
        with open(str(tmp_path / "briefings.json")) as f:
            data = json.load(f)
        assert len(data) == 1

    def test_briefings_accumulate_up_to_30(self, tmp_path: Path) -> None:
        """After 30 save_briefing calls, the file contains exactly 30 entries."""
        storage = _make_storage(tmp_path)
        for i in range(30):
            storage.save_briefing(_make_briefing(title=f"Article {i}"))
        with open(str(tmp_path / "briefings.json")) as f:
            data = json.load(f)
        assert len(data) == 30

    def test_31st_briefing_does_not_exceed_limit(self, tmp_path: Path) -> None:
        """After 31 save_briefing calls, the file still contains exactly 30 entries."""
        storage = _make_storage(tmp_path)
        for i in range(31):
            storage.save_briefing(_make_briefing(title=f"Article {i}"))
        with open(str(tmp_path / "briefings.json")) as f:
            data = json.load(f)
        assert len(data) == 30

    def test_35_briefings_retains_only_last_30(self, tmp_path: Path) -> None:
        """After 35 save_briefing calls, the file contains exactly 30 entries."""
        storage = _make_storage(tmp_path)
        for i in range(35):
            storage.save_briefing(_make_briefing(title=f"Article {i}"))
        with open(str(tmp_path / "briefings.json")) as f:
            data = json.load(f)
        assert len(data) == 30

    def test_oldest_briefings_are_discarded(self, tmp_path: Path) -> None:
        """When the limit is exceeded, the oldest entries are dropped, not the newest."""
        storage = _make_storage(tmp_path)
        for i in range(35):
            storage.save_briefing(_make_briefing(title=f"Article {i}"))
        with open(str(tmp_path / "briefings.json")) as f:
            data = json.load(f)
        titles = [entry["topics"][0]["articles"][0]["title"] for entry in data]
        assert "Article 0" not in titles
        assert "Article 34" in titles

    def test_briefing_contains_generated_at(self, tmp_path: Path) -> None:
        """Each saved briefing entry includes a 'generated_at' ISO timestamp."""
        storage = _make_storage(tmp_path)
        storage.save_briefing(_make_briefing())
        with open(str(tmp_path / "briefings.json")) as f:
            data = json.load(f)
        assert "generated_at" in data[0]

    def test_briefing_article_fields_are_persisted(self, tmp_path: Path) -> None:
        """Article fields (title, summary, url, source) are written to the briefings file."""
        storage = _make_storage(tmp_path)
        article = Article(
            title="Test Title",
            summary="Test Summary",
            url="https://test.com",
            source="Test Source",
        )
        briefing = Briefing(
            topics=[TopicBriefing(topic="tech", articles=[article])]
        )
        storage.save_briefing(briefing)
        with open(str(tmp_path / "briefings.json")) as f:
            data = json.load(f)
        saved_article = data[0]["topics"][0]["articles"][0]
        assert saved_article["title"] == "Test Title"
        assert saved_article["summary"] == "Test Summary"
        assert saved_article["url"] == "https://test.com"
        assert saved_article["source"] == "Test Source"

    def test_save_briefing_creates_file_if_not_exists(self, tmp_path: Path) -> None:
        """save_briefing() creates the briefings file from scratch if it does not exist."""
        storage = _make_storage(tmp_path)
        briefings_path = tmp_path / "briefings.json"
        assert not briefings_path.exists()
        storage.save_briefing(_make_briefing())
        assert briefings_path.exists()
