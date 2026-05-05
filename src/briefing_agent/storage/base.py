from abc import ABC, abstractmethod

from briefing_agent.models.briefing import Briefing
from briefing_agent.models.preferences import UserPreferences


class BaseStorage(ABC):
    """Abstract base class for application storage."""

    @abstractmethod
    def save(self, preferences: UserPreferences) -> None:
        """Save user preferences to storage."""
        ...

    @abstractmethod
    def load(self) -> UserPreferences | None:
        """Load user preferences from storage."""
        ...

    @abstractmethod
    def save_briefing(self, briefing: Briefing) -> None:
        """Save a generated briefing to storage."""
        ...
