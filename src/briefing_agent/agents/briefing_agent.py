from agno.agent import Agent
from agno.models.groq import Groq

from briefing_agent.agents.base import BaseAgent
from briefing_agent.models.briefing import Briefing, TopicBriefing
from briefing_agent.models.preferences import UserPreferences
from briefing_agent.tools.discord_sender import DiscordSender
from briefing_agent.tools.email_sender import EmailSender
from briefing_agent.tools.news_fetcher import NewsFetcher
from briefing_agent.storage.base import BaseStorage


BRIEFING_INSTRUCTIONS = """
You are a news briefing assistant. Given a list of articles for a topic,
generate a concise and informative summary in the same language as the articles.
Structure the summary with:
- A short introduction of the topic
- Key highlights from the articles
- A brief closing remark
Keep it professional and objective.
"""


class BriefingAgent(BaseAgent):
    """Agent responsible for generating and distributing the news briefing."""

    def __init__(
        self,
        news_fetcher: NewsFetcher,
        email_sender: EmailSender,
        discord_sender: DiscordSender,
        storage: BaseStorage = None,
    ) -> None:
        """Initialize with tool dependencies via injection."""
        self._fetcher = news_fetcher
        self._email_sender = email_sender
        self._discord_sender = discord_sender
        self._storage = storage
        self._agent = Agent(
            model=Groq(id="llama-3.3-70b-versatile"),
            instructions=BRIEFING_INSTRUCTIONS,
            markdown=False,
        )

    def run(self, preferences: UserPreferences) -> Briefing:
        """Fetch news, generate briefing and distribute it."""
        briefing = self._build_briefing(preferences)
        content = self._format_briefing(briefing)
        self._distribute(content, preferences)
        
        # Salva o briefing no JSON
        if self._storage:
            self._storage.save_briefing(briefing)
        
        return briefing

    def _build_briefing(self, preferences: UserPreferences) -> Briefing:
        """Fetch articles for each topic and build the Briefing object."""
        topics = [
            TopicBriefing(
                topic=topic.name,
                articles=self._fetcher.run(
                    topic.name, topic.keywords, topic.max_articles
                ),
            )
            for topic in preferences.topics
        ]
        return Briefing(topics=topics)

    def _format_briefing(self, briefing: Briefing) -> str:
        """Use the AI agent to format the briefing into readable text."""
        raw = "\n\n".join(
            f"Topic: {t.topic}\n" +
            "\n".join(f"- {a.title}: {a.summary}" for a in t.articles)
            for t in briefing.topics
        )
        response = self._agent.run(f"Format this briefing:\n{raw}")
        return response.content

    def _distribute(self, content: str, preferences: UserPreferences) -> None:
        """Send the briefing via email and Discord."""
        self._email_sender.run(preferences.email, "Your Daily Briefing", content)
        self._discord_sender.run(preferences.discord_channel_id, content)
