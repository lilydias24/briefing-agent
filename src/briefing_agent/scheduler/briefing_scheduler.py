# ... (resto do código igual)

    def start(self) -> None:
        """Start the scheduler."""
        # Agenda para rodar às 7 da manhã
        self._scheduler.add_job(
            self._run_briefing,
            'cron',
            hour=7,
            minute=0,
            id='briefing_job',
        )
        self._scheduler.start()
        print(f"✅ Scheduler iniciado! Rodando diariamente às 7:00.")
