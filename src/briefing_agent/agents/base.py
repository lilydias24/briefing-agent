from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def run(self, *args, **kwargs):
        """Execute the agent's main action."""
        ...