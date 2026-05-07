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
    preferences = storage.load()
    hour = preferences.schedule_hour if preferences else 1
    minute = preferences.schedule_minute if preferences else 0
    
    return BriefingScheduler(
        agent=agent,
        storage=storage,
        hour=hour,
        minute=minute,
    )


def main() -> None:
    """Load environment variables and start the scheduler and Discord bot concurrently."""
    load_dotenv()

    storage = JsonStorage()
    preferences = storage.load()
    
    if preferences:
        print(f"✅ Preferences loaded: {preferences.email} | Schedule: {preferences.schedule_hour:02d}:{preferences.schedule_minute:02d}")
    else:
        print("⚠️  No preferences found. Starting setup mode...")
    
    setup_agent = SetupAgent(storage=storage)
    briefing_agent = build_briefing_agent(storage)
    scheduler = build_scheduler(briefing_agent, storage)

    # Attach scheduler to setup agent so it can request reschedules after setup
    setup_agent.attach_scheduler(scheduler)

    # APScheduler manages its own background thread, so start it directly here.
    scheduler.start()
    print(f"🚀 Scheduler initialized (time: {scheduler._hour:02d}:{scheduler._minute:02d})")

    # Start Discord bot in a background thread because bot.run() is blocking.
    print("🤖 Starting Discord bot in background thread...")
    bot_thread = threading.Thread(target=run_bot, args=(setup_agent,), daemon=False, name="BotThread")
    bot_thread.start()

    # Keep the process alive and only monitor the bot thread.
    try:
        bot_thread.join()
        print("[main] Bot thread finished.")
    except KeyboardInterrupt:
        print("\n[main] Shutdown signal received. Stopping scheduler and bot...")
        scheduler.stop()
        print("[main] Scheduler stopped.")
        # Bot will stop gracefully on its own when threads join
        bot_thread.join(timeout=5)
        print("[main] All threads stopped. Goodbye!")


if __name__ == "__main__":
    main()
