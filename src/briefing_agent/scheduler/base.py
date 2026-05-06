from abc import ABC, abstractmethod


class BaseScheduler(ABC):
    """Abstract base class for briefing schedulers."""

    @abstractmethod
    def start(self) -> None:
        """Start the scheduler."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Stop the scheduler."""
        ...