#Define a interface abstrata de storage — seguindo DIP e ISP, o sistema depende dessa abstração, não de uma implementação concreta:

from abc import ABC, abstractmethod

from briefing_agent.models.preferences import UserPreferences


class BaseStorage(ABC):
    """Abstract base class for user preferences storage."""

    @abstractmethod
    def save(self, preferences: UserPreferences) -> None:
        """Save user preferences to storage."""
        ...

    @abstractmethod
    def load(self) -> UserPreferences | None:
        """Load user preferences from storage."""
        ...