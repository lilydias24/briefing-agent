#Este arquivo define a ferramenta de busca de notícias. Ele é responsável por buscar notícias recentes sobre os tópicos de interesse do usuário, usando uma API de notícias. A ferramenta recebe um tópico e uma lista de palavras-chave, e retorna uma lista de artigos relacionados a esse tópico, filtrados pelas palavras-chave. A implementação atual usa a NewsAPI, mas a gente pode trocar por outra API no futuro se for necessário. O importante é que a ferramenta seja fácil de usar e que retorne os dados em um formato consistente, para que o agente possa processar as informações de forma eficiente.

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
        # terms = [topic] + keywords
        # return " OR ".join(terms)
        return keywords

    def _request(self, query: str, max_articles: int) -> dict:
        """Send HTTP request to NewsAPI and return parsed JSON."""
        params = {
            "q": query,
            "pageSize": max_articles,
            "sortBy": "publishedAt",
            "language": "pt",
            "apiKey": self._api_key,
        }
        response = httpx.get(self.BASE_URL, params=params, timeout=10)
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