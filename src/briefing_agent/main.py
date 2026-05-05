import threading

from dotenv import load_dotenv

from briefing_agent.agents.briefing_agent import BriefingAgent
from briefing_agent.agents.setup_agent import SetupAgent
from briefing_agent.bot import run_bot
from briefing_agent.scheduler.briefing_scheduler import BriefingScheduler
from briefing_agent.storage.json_storage import JsonStorage
from briefing_agent.tools.discord_sender import DiscordSender
from briefing_agent.tools.email_sender import EmailSender
from briefing_agent.tools.news_fetcher import NewsFetcher


def build_briefing_agent(storage: JsonStorage) -> BriefingAgent:
    """Instantiate and wire all dependencies for the briefing agent."""
    return BriefingAgent(
        news_fetcher=NewsFetcher(),
        email_sender=EmailSender(),
        discord_sender=DiscordSender(),
        storage=storage,
    )


def build_scheduler(agent: BriefingAgent, storage: JsonStorage) -> BriefingScheduler:
    """Instantiate the scheduler with storage and agent dependencies."""
    return BriefingScheduler(
        agent=agent,
        storage=storage,
        hour=1,
        minute=0,
    )


def main() -> None:
    """Load environment variables and start the scheduler and Discord bot."""
    load_dotenv()

    storage = JsonStorage()
    setup_agent = SetupAgent(storage=storage)
    briefing_agent = build_briefing_agent(storage)
    scheduler = build_scheduler(briefing_agent, storage)

    scheduler_thread = threading.Thread(target=scheduler.start, daemon=True)
    scheduler_thread.start()

    run_bot(setup_agent)


if __name__ == "__main__":
    main()
