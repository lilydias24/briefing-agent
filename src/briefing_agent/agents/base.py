from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute the agent's main action."""
        ...