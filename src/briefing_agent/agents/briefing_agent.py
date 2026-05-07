from typing import Any

from agno.agent import Agent
from agno.models.groq import Groq

from briefing_agent.agents.base import BaseAgent
from briefing_agent.models.briefing import Briefing, TopicBriefing
from briefing_agent.models.preferences import UserPreferences
from briefing_agent.storage.base import BaseStorage
from briefing_agent.tools.discord_sender import DiscordSender
from briefing_agent.tools.email_sender import EmailSender
from briefing_agent.tools.news_fetcher import NewsFetcher


BRIEFING_INSTRUCTIONS = """
You are a news briefing assistant. Given a list of articles grouped by topic,
generate a concise, professional and objective daily briefing.

The briefing must include:
- A short introduction
- The main highlights grouped by topic
- A brief closing remark

Keep the language clear and avoid unnecessary details.
"""


class BriefingAgent(BaseAgent):
    """Agent responsible for generating, storing and distributing news briefings."""

    def __init__(
        self,
        news_fetcher: NewsFetcher,
        email_sender: EmailSender,
        discord_sender: DiscordSender,
        storage: BaseStorage | None = None,
    ) -> None:
        """Initialize the briefing agent with its required dependencies."""
        self._news_fetcher = news_fetcher
        self._email_sender = email_sender
        self._discord_sender = discord_sender
        self._storage = storage
        self._agent = Agent(
            model=Groq(id="llama-3.3-70b-versatile"),
            instructions=BRIEFING_INSTRUCTIONS,
            markdown=False,
        )

    def run(self, preferences: UserPreferences) -> Briefing:
        """Generate a briefing from user preferences and send it to the user."""
        briefing = self._build_briefing(preferences)
        content = self._format_briefing(briefing)

        self._send_briefing(content, preferences)

        if self._storage is not None:
            self._storage.save_briefing(briefing)

        return briefing

    def _build_briefing(self, preferences: UserPreferences) -> Briefing:
        """Fetch articles for each configured topic."""
        topics = []

        for topic in preferences.topics:
            articles = self._news_fetcher.run(
                topic=topic.name,
                keywords=topic.keywords,
                max_articles=topic.max_articles,
            )

            topics.append(
                TopicBriefing(
                    topic=topic.name,
                    articles=articles,
                )
            )

        return Briefing(topics=topics)

    def _format_briefing(self, briefing: Briefing) -> str:
        """Format the briefing using the LLM."""
        raw_briefing = self._build_raw_briefing_text(briefing)

        if not raw_briefing.strip():
            return "No articles were found for the configured topics."

        response = self._agent.run(f"Format this briefing:\n\n{raw_briefing}")

        return self._extract_response_content(response)

    def _build_raw_briefing_text(self, briefing: Briefing) -> str:
        """Build a plain text version of the collected articles."""
        sections = []

        for topic in briefing.topics:
            article_lines = []

            for article in topic.articles:
                article_lines.append(
                    f"- {article.title}\n"
                    f"  Source: {article.source}\n"
                    f"  Summary: {article.summary}\n"
                    f"  URL: {article.url}"
                )

            if article_lines:
                sections.append(
                    f"Topic: {topic.topic}\n" + "\n".join(article_lines)
                )

        return "\n\n".join(sections)

    def _extract_response_content(self, response: Any) -> str:
        """Extract text from different Agno response formats."""
        content = getattr(response, "content", None)

        if content is not None:
            return str(content)

        message = getattr(response, "message", None)

        if message is not None:
            return str(message)

        return str(response)

    def _send_briefing(self, content: str, preferences: UserPreferences) -> None:
        """Send the generated briefing by email and Discord."""
        self._email_sender.run(
            preferences.email,
            "Seu Resumo Diário",
            content,
        )

        self._discord_sender.run(
            preferences.discord_channel_id,
            content,
        )
