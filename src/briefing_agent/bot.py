#Este arquivo define o bot do Discord, que é a interface de chat usada para coletar as preferências do usuário para o briefing. O bot é responsável por receber mensagens dos usuários, processá-las usando o SetupAgent, e responder com as informações necessárias para configurar o briefing. Ele usa a biblioteca discord.py para se conectar ao Discord e interagir com os usuários de forma eficiente. O bot é projetado para ser fácil de usar e manter, garantindo que os usuários possam configurar seus briefings de forma rápida e intuitiva.

import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from briefing_agent.agents.setup_agent import SetupAgent
from briefing_agent.models.preferences import UserPreferences
from briefing_agent.storage.json_storage import JsonStorage

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
storage = JsonStorage()
setup_agent = SetupAgent(storage=storage)
pending_preferences: dict[int, UserPreferences] = {}


@bot.event
async def on_ready() -> None:
    """Log when the bot is connected and ready."""
    print(f"Bot connected as {bot.user}")


@bot.event
async def on_message(message: discord.Message) -> None:
    """Handle incoming messages and forward to setup agent."""
    if message.author.bot:
        return
    response = setup_agent.run(message.content)
    await message.channel.send(response)
    await bot.process_commands(message)


def run_bot() -> None:
    """Start the Discord bot."""
    bot.run(os.getenv("DISCORD_BOT_TOKEN", ""))