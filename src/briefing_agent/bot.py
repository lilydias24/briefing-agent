import os

import discord
from discord.ext import commands

from briefing_agent.agents.setup_agent import SetupAgent


def create_bot(setup_agent: SetupAgent) -> commands.Bot:
    """Create and configure the Discord bot with injected dependencies."""
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready() -> None:
        """Log when the bot is connected and ready."""
        print(f"Bot connected as {bot.user}")

    @bot.event
    async def on_message(message: discord.Message) -> None:
        """Handle incoming messages and forward them to the setup agent."""
        if message.author.bot:
            return

        response = setup_agent.run(message.content, session_id=str(message.author.id))
        await message.channel.send(response)
        await bot.process_commands(message)

    return bot


def run_bot(setup_agent: SetupAgent) -> None:
    """Start the Discord bot using the provided setup agent dependency."""
    token = os.getenv("DISCORD_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not configured.")

    bot = create_bot(setup_agent)
    bot.run(token)
