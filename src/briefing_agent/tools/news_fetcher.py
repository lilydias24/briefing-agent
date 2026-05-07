import os
import httpx

from briefing_agent.models.briefing import Article
from briefing_agent.tools.base import BaseTool


class NewsFetcher(BaseTool):
    """Fetches recent news articles from NewsAPI."""

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self) -> None:
        """Initialize with API key from environment."""
        self._api_key = os.getenv("NEWS_API_KEY", "")

    def run(self, topic: str, keywords: list[str], max_articles: int) -> list[Article]:
        """Fetch articles for a topic filtered by keywords."""
        query = self._build_query(topic, keywords)
        print(f"Fetching news with query: {query}")
        response = self._request(query, max_articles)
        print(f"Received {len(response.get('articles', []))} articles from API")
        return self._parse_articles(response)

    def _build_query(self, topic: str, keywords: list[str]) -> str:
        """Build the search query string from topic and keywords."""
        def _quote(term: str) -> str:
            if not term:
                return ""
            # remove stray double-quotes and wrap multi-word terms in quotes
            term = term.replace('"', '')
            return f'"{term}"' if " " in term else term

        topic_q = _quote(topic)
        # Filter out empty keywords and deduplicate while preserving order
        seen = set()
        kws = []
        for k in keywords:
            if not k:
                continue
            k = k.strip()
            if not k or k in seen or k == topic:
                continue
            seen.add(k)
            kws.append(_quote(k))

        if kws:
            # require the topic AND at least one of the keywords
            return f"{topic_q} AND ({' OR '.join(kws)})"

        return topic_q
  

    def _request(self, query: str, max_articles: int) -> dict:
        """Send HTTP request to NewsAPI and return parsed JSON."""
        params = {
            "q": query,
            "pageSize": max_articles,
            "sortBy": "publishedAt",
            "language": "pt",
            "apiKey": self._api_key,
        }
        # Allow configuring SSL verification via environment variable:
        # - If NEWS_API_VERIFY is "false" (case-insensitive) verification is disabled (not recommended).
        # - If NEWS_API_VERIFY is a path to a CA bundle file, it will be used.
        verify_env = os.getenv("NEWS_API_VERIFY", "").strip()
        if verify_env:
            if verify_env.lower() in ("false", "0", "no", "off"):
                verify = False
            else:
                verify = verify_env
        else:
            verify = True

        print(f"HTTP verify setting: {verify}")
        response = httpx.get(self.BASE_URL, params=params, timeout=10, verify=verify)
        response.raise_for_status()
        return response.json()

    def _parse_articles(self, data: dict) -> list[Article]:
        """Parse raw API response into a list of Article instances."""
        return [
            Article(
                title=item.get("title", ""),
                summary=item.get("description", ""),
                url=item.get("url", ""),
                source=item.get("source", {}).get("name", ""),
            )
            for item in data.get("articles", [])
        ]