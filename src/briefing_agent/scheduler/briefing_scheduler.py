import traceback
from apscheduler.schedulers.background import BackgroundScheduler

from briefing_agent.agents.briefing_agent import BriefingAgent
from briefing_agent.scheduler.base import BaseScheduler
from briefing_agent.storage.base import BaseStorage


class BriefingScheduler(BaseScheduler):
    """Schedules the briefing agent to run at a specific time each day."""

    def __init__(
        self,
        agent: BriefingAgent,
        storage: BaseStorage,
        hour: int = 7,
        minute: int = 0,
    ) -> None:
        """Initialize the scheduler with agent and storage dependencies."""
        self._agent = agent
        self._storage = storage
        self._hour = hour
        self._minute = minute
        self._scheduler = BackgroundScheduler()

    def start(self) -> None:
        """Start the scheduler."""
        self._scheduler.add_job(
            self._run_briefing,
            'cron',
            hour=self._hour,
            minute=self._minute,
            id='briefing_job',
        )
        self._scheduler.start()
        print(f"Scheduler started! Running daily at {self._hour}:{self._minute:02d}.")

    def stop(self) -> None:
        """Stop the scheduler."""
        self._scheduler.shutdown()
        print("Scheduler stopped.")

    def _run_briefing(self) -> None:
        """Execute the briefing agent."""
        try:
            preferences = self._storage.load()
            if not preferences:
                print("No user preferences found. Skipping briefing.")
                return
                
            self._agent.run(preferences)
            print("Briefing generated and sent!")
        except Exception as e:
            print(f"Error generating briefing: {e}")
            traceback.print_exc()