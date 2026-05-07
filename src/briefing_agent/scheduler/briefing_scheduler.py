import traceback
from apscheduler.schedulers.background import BackgroundScheduler

from briefing_agent.agents.briefing_agent import BriefingAgent
from briefing_agent.scheduler.base import BaseScheduler
from briefing_agent.storage.base import BaseStorage
from datetime import datetime


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
        self._started = False

    def start(self) -> None:
        """Start the scheduler."""
        if self._started:
            print("Scheduler already started; skipping start().")
            return

        # Ensure only one job with the same id exists; replace if present
        self._scheduler.add_job(
            self._run_briefing,
            'cron',
            hour=self._hour,
            minute=self._minute,
            id='briefing_job',
            replace_existing=True,
            coalesce=True,
            misfire_grace_time=300,
        )
        self._scheduler.start()
        self._started = True
        now = datetime.now().isoformat(sep=' ', timespec='seconds')
        print(f"[{now}] Scheduler started! Running daily at {self._hour:02d}:{self._minute:02d}.")

    def stop(self) -> None:
        """Stop the scheduler."""
        try:
            self._scheduler.shutdown()
            print("Scheduler stopped.")
        finally:
            self._started = False

    def _run_briefing(self) -> None:
        """Execute the briefing agent."""
        try:
            start_ts = datetime.now().isoformat(sep=' ', timespec='seconds')
            print(f"[{start_ts}] Running scheduled briefing job (id=briefing_job)...")

            preferences = self._storage.load()
            if not preferences:
                print(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] No user preferences found. Skipping briefing.")
                return

            self._agent.run(preferences)
            end_ts = datetime.now().isoformat(sep=' ', timespec='seconds')
            print(f"[{end_ts}] Briefing generated and sent!")
        except Exception as e:
            print(f"Error generating briefing: {e}")
            traceback.print_exc()

    def reschedule(self) -> None:
        """Reload preferences from storage and update the scheduled job time.

        This allows updating the schedule at runtime after preferences change.
        """
        prefs = self._storage.load()
        if not prefs:
            print(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] No preferences available to reschedule.")
            return

        new_hour = prefs.schedule_hour
        new_minute = prefs.schedule_minute
        self._hour = new_hour
        self._minute = new_minute

        # Replace existing job with new schedule
        self._scheduler.add_job(
            self._run_briefing,
            'cron',
            hour=self._hour,
            minute=self._minute,
            id='briefing_job',
            replace_existing=True,
            coalesce=True,
            misfire_grace_time=300,
        )
        print(f"[{datetime.now().isoformat(sep=' ', timespec='seconds')}] Scheduler rescheduled to {self._hour:02d}:{self._minute:02d}.")