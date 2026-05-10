from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from briefing_agent.models.briefing import Article
from briefing_agent.tools.news_fetcher import NewsFetcher


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fetcher() -> NewsFetcher:
    """Return a NewsFetcher with an empty API key (HTTP calls must be mocked)."""
    return NewsFetcher()


SAMPLE_RESPONSE: dict = {
    "articles": [
        {
            "title": "Article One",
            "description": "Summary one",
            "url": "https://example.com/1",
            "source": {"name": "Source A"},
        },
        {
            "title": "Article Two",
            "description": "Summary two",
            "url": "https://example.com/2",
            "source": {"name": "Source B"},
        },
        {
            "title": "Article Three",
            "description": "Summary three",
            "url": "https://example.com/3",
            "source": {"name": "Source C"},
        },
    ]
}


def _make_http_response(data: dict) -> MagicMock:
    """Build a mock object that mimics an httpx Response."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = data
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


# ---------------------------------------------------------------------------
# _build_query
# ---------------------------------------------------------------------------

class TestBuildQuery:
    """Tests for NewsFetcher._build_query."""

    def test_returns_string(self, fetcher: NewsFetcher) -> None:
        """_build_query always returns a str, never a list or other type."""
        result = fetcher._build_query("technology", ["AI", "ML"])
        assert isinstance(result, str)

    def test_empty_keywords_returns_topic_only(self, fetcher: NewsFetcher) -> None:
        """With no keywords the query is exactly the topic string."""
        result = fetcher._build_query("energy", [])
        assert result == "energy"

    def test_empty_keywords_has_no_and_operator(self, fetcher: NewsFetcher) -> None:
        """With no keywords the query does not contain an AND operator."""
        result = fetcher._build_query("energy", [])
        assert "AND" not in result

    def test_with_keywords_contains_topic(self, fetcher: NewsFetcher) -> None:
        """The topic always appears in the query string."""
        result = fetcher._build_query("technology", ["AI", "ML"])
        assert "technology" in result

    def test_with_keywords_uses_and_or_structure(self, fetcher: NewsFetcher) -> None:
        """Keywords are combined with AND/OR so both operators appear in the query."""
        result = fetcher._build_query("technology", ["AI", "ML"])
        assert "AND" in result
        assert "OR" in result

    def test_single_keyword(self, fetcher: NewsFetcher) -> None:
        """A single keyword produces a query containing both the topic and the keyword."""
        result = fetcher._build_query("energy", ["solar"])
        assert "energy" in result
        assert "solar" in result
        assert "AND" in result

    def test_multi_word_keyword_is_quoted(self, fetcher: NewsFetcher) -> None:
        """Multi-word keywords are wrapped in double quotes in the query."""
        result = fetcher._build_query("technology", ["smart grid"])
        assert '"smart grid"' in result

    def test_single_word_keyword_is_not_quoted(self, fetcher: NewsFetcher) -> None:
        """Single-word keywords are NOT wrapped in double quotes."""
        result = fetcher._build_query("technology", ["AI"])
        assert '"AI"' not in result
        assert "AI" in result

    def test_keyword_equal_to_topic_is_excluded(self, fetcher: NewsFetcher) -> None:
        """A keyword identical to the topic is excluded to avoid duplication."""
        result = fetcher._build_query("energy", ["energy", "solar"])
        assert result.count("energy") == 1
        assert "solar" in result

    def test_blank_keywords_are_filtered_out(self, fetcher: NewsFetcher) -> None:
        """Empty and whitespace-only keywords are silently ignored."""
        result = fetcher._build_query("energy", ["", "  ", "solar"])
        assert "solar" in result
        assert "AND" in result

    def test_all_blank_keywords_falls_back_to_topic_only(self, fetcher: NewsFetcher) -> None:
        """When all keywords are blank the query falls back to the topic only."""
        result = fetcher._build_query("energy", ["", "  "])
        assert result == "energy"

    def test_duplicate_keywords_deduplicated(self, fetcher: NewsFetcher) -> None:
        """Duplicate keywords appear only once in the query."""
        result = fetcher._build_query("tech", ["AI", "AI", "ML"])
        assert result.count("AI") == 1


# ---------------------------------------------------------------------------
# _parse_articles
# ---------------------------------------------------------------------------

class TestParseArticles:
    """Tests for NewsFetcher._parse_articles."""

    def test_returns_list_of_article_instances(self, fetcher: NewsFetcher) -> None:
        """_parse_articles returns a list of Article dataclass instances."""
        result = fetcher._parse_articles(SAMPLE_RESPONSE)
        assert isinstance(result, list)
        assert all(isinstance(a, Article) for a in result)

    def test_correct_article_count(self, fetcher: NewsFetcher) -> None:
        """The number of returned articles matches the number in the API response."""
        result = fetcher._parse_articles(SAMPLE_RESPONSE)
        assert len(result) == 3

    def test_article_title_mapped_correctly(self, fetcher: NewsFetcher) -> None:
        """The 'title' field from the API response maps to Article.title."""
        result = fetcher._parse_articles(SAMPLE_RESPONSE)
        assert result[0].title == "Article One"

    def test_article_summary_mapped_from_description(self, fetcher: NewsFetcher) -> None:
        """The 'description' field from the API response maps to Article.summary."""
        result = fetcher._parse_articles(SAMPLE_RESPONSE)
        assert result[0].summary == "Summary one"

    def test_article_url_mapped_correctly(self, fetcher: NewsFetcher) -> None:
        """The 'url' field from the API response maps to Article.url."""
        result = fetcher._parse_articles(SAMPLE_RESPONSE)
        assert result[0].url == "https://example.com/1"

    def test_article_source_name_mapped_correctly(self, fetcher: NewsFetcher) -> None:
        """The nested 'source.name' field maps to Article.source."""
        result = fetcher._parse_articles(SAMPLE_RESPONSE)
        assert result[0].source == "Source A"

    def test_empty_articles_list_returns_empty(self, fetcher: NewsFetcher) -> None:
        """An empty articles array in the response returns an empty list."""
        result = fetcher._parse_articles({"articles": []})
        assert result == []

    def test_missing_articles_key_returns_empty(self, fetcher: NewsFetcher) -> None:
        """A response without the 'articles' key returns an empty list."""
        result = fetcher._parse_articles({})
        assert result == []

    def test_missing_title_defaults_to_empty_string(self, fetcher: NewsFetcher) -> None:
        """Article.title defaults to '' when the field is absent from the response."""
        data = {"articles": [{"description": "S", "url": "https://a.com", "source": {"name": "X"}}]}
        result = fetcher._parse_articles(data)
        assert result[0].title == ""

    def test_missing_description_defaults_to_empty_string(self, fetcher: NewsFetcher) -> None:
        """Article.summary defaults to '' when 'description' is absent from the response."""
        data = {"articles": [{"title": "T", "url": "https://a.com", "source": {"name": "X"}}]}
        result = fetcher._parse_articles(data)
        assert result[0].summary == ""

    def test_missing_url_defaults_to_empty_string(self, fetcher: NewsFetcher) -> None:
        """Article.url defaults to '' when the field is absent from the response."""
        data = {"articles": [{"title": "T", "description": "S", "source": {"name": "X"}}]}
        result = fetcher._parse_articles(data)
        assert result[0].url == ""

    def test_missing_source_defaults_to_empty_string(self, fetcher: NewsFetcher) -> None:
        """Article.source defaults to '' when the 'source' object is absent."""
        data = {"articles": [{"title": "T", "description": "S", "url": "https://a.com"}]}
        result = fetcher._parse_articles(data)
        assert result[0].source == ""

    def test_missing_source_name_defaults_to_empty_string(self, fetcher: NewsFetcher) -> None:
        """Article.source defaults to '' when 'source.name' is absent."""
        data = {"articles": [{"title": "T", "description": "S", "url": "https://a.com", "source": {}}]}
        result = fetcher._parse_articles(data)
        assert result[0].source == ""

    def test_order_of_articles_preserved(self, fetcher: NewsFetcher) -> None:
        """Articles are returned in the same order they appear in the API response."""
        result = fetcher._parse_articles(SAMPLE_RESPONSE)
        assert result[0].title == "Article One"
        assert result[1].title == "Article Two"
        assert result[2].title == "Article Three"


# ---------------------------------------------------------------------------
# run() with mocked HTTP
# ---------------------------------------------------------------------------

class TestRunWithMockHttp:
    """Integration tests for NewsFetcher.run() with httpx.get mocked."""

    def test_run_returns_list_of_articles(self, fetcher: NewsFetcher) -> None:
        """run() returns a list of Article instances parsed from the API response."""
        mock_resp = _make_http_response(SAMPLE_RESPONSE)
        with patch("httpx.get", return_value=mock_resp):
            result = fetcher.run("technology", ["AI"], 5)
        assert isinstance(result, list)
        assert all(isinstance(a, Article) for a in result)

    def test_run_returns_correct_article_count(self, fetcher: NewsFetcher) -> None:
        """run() returns one Article per item in the API response."""
        mock_resp = _make_http_response(SAMPLE_RESPONSE)
        with patch("httpx.get", return_value=mock_resp):
            result = fetcher.run("technology", ["AI"], 5)
        assert len(result) == 3

    def test_run_maps_article_fields(self, fetcher: NewsFetcher) -> None:
        """Article fields returned by run() match the values from the API response."""
        mock_resp = _make_http_response(SAMPLE_RESPONSE)
        with patch("httpx.get", return_value=mock_resp):
            result = fetcher.run("technology", ["AI"], 5)
        assert result[0].title == "Article One"
        assert result[0].summary == "Summary one"
        assert result[0].source == "Source A"

    def test_run_empty_response_returns_empty_list(self, fetcher: NewsFetcher) -> None:
        """run() returns an empty list when the API responds with no articles."""
        mock_resp = _make_http_response({"articles": []})
        with patch("httpx.get", return_value=mock_resp):
            result = fetcher.run("technology", [], 5)
        assert result == []

    def test_run_passes_max_articles_as_page_size(self, fetcher: NewsFetcher) -> None:
        """run() forwards max_articles to the API as the 'pageSize' parameter."""
        mock_resp = _make_http_response(SAMPLE_RESPONSE)
        with patch("httpx.get", return_value=mock_resp) as mock_get:
            fetcher.run("technology", ["AI"], 3)
        params = mock_get.call_args.kwargs["params"]
        assert params["pageSize"] == 3

    def test_run_passes_topic_in_query(self, fetcher: NewsFetcher) -> None:
        """The topic name appears inside the 'q' parameter sent to the API."""
        mock_resp = _make_http_response({"articles": []})
        with patch("httpx.get", return_value=mock_resp) as mock_get:
            fetcher.run("energy", [], 5)
        params = mock_get.call_args.kwargs["params"]
        assert "energy" in params["q"]

    def test_run_calls_raise_for_status(self, fetcher: NewsFetcher) -> None:
        """run() calls raise_for_status() to surface HTTP error codes."""
        mock_resp = _make_http_response(SAMPLE_RESPONSE)
        with patch("httpx.get", return_value=mock_resp):
            fetcher.run("technology", [], 5)
        mock_resp.raise_for_status.assert_called_once()

    def test_run_sends_api_key_from_env(self, fetcher: NewsFetcher, monkeypatch: pytest.MonkeyPatch) -> None:
        """run() reads NEWS_API_KEY from the environment and includes it in the request."""
        monkeypatch.setenv("NEWS_API_KEY", "test-key-xyz")
        fetcher_with_key = NewsFetcher()
        mock_resp = _make_http_response({"articles": []})
        with patch("httpx.get", return_value=mock_resp) as mock_get:
            fetcher_with_key.run("energy", [], 5)
        params = mock_get.call_args.kwargs["params"]
        assert params["apiKey"] == "test-key-xyz"

    def test_run_requests_english_language(self, fetcher: NewsFetcher) -> None:
        """run() always requests English ('en') articles from the API."""
        mock_resp = _make_http_response({"articles": []})
        with patch("httpx.get", return_value=mock_resp) as mock_get:
            fetcher.run("technology", [], 5)
        params = mock_get.call_args.kwargs["params"]
        assert params["language"] == "en"

    def test_run_with_no_keywords_still_works(self, fetcher: NewsFetcher) -> None:
        """run() succeeds and returns articles even when the keywords list is empty."""
        mock_resp = _make_http_response(SAMPLE_RESPONSE)
        with patch("httpx.get", return_value=mock_resp):
            result = fetcher.run("energy", [], 5)
        assert len(result) == 3
