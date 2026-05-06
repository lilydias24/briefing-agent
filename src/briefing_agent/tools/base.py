from abc import ABC, abstractmethod


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    @abstractmethod
    def run(self, *args, **kwargs):
        """Execute the tool's main action."""
        ...