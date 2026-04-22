from agno.agent import Agent
from agno.models.groq import Groq

from briefing_agent.agents.base import BaseAgent
from briefing_agent.models.preferences import UserPreferences
from briefing_agent.storage.base import BaseStorage


SETUP_INSTRUCTIONS = """
You are collecting user preferences for a news briefing system.
Ask ONE question at a time, very briefly (1-2 sentences max).
Current step:
1. Ask for topics (comma-separated)
2. Ask for keywords
3. Ask for max articles per topic
4. Ask for email
5. Ask for Discord channel ID

Keep it SHORT and direct. No confirmations or repetitions.
"""


class SetupAgent(BaseAgent):
    """Agent responsible for collecting user preferences via Discord chat."""

    def __init__(self, storage: BaseStorage) -> None:
        """Initialize with a storage dependency for saving preferences."""
        self._storage = storage
        self._conversation_history = []
        self._agent = Agent(
            model=Groq(id="llama-3.3-70b-versatile"),
            instructions=SETUP_INSTRUCTIONS,
            markdown=False,
        )

    def run(self, user_message: str) -> str:
        """Process a user message and return the agent's response."""
        # Add user message to history
        self._conversation_history.append({"role": "user", "content": user_message})
        
        # Build context from history
        context = "Conversation history:\n"
        for msg in self._conversation_history[-10:]:  # Keep last 10 messages
            context += f"{msg['role']}: {msg['content']}\n"
        
        # Get response
        full_prompt = context + "\nRespond to the user:"
        response = self._agent.run(full_prompt)
        
        # Add agent response to history
        self._conversation_history.append({"role": "assistant", "content": response.content})
        
        return response.content

    def save_preferences(self, preferences: UserPreferences) -> None:
        """Persist the collected user preferences."""
        self._storage.save(preferences)
