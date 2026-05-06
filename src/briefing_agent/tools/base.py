from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for all agent tools."""

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Execute the tool's main action."""
        ...