#Esse arquivo define a ferramenta de envio de mensagens para o Discord. Ele é responsável por enviar o briefing final para um canal do Discord, usando a API do Discord. A ferramenta recebe o ID do canal e o conteúdo da mensagem, e se conecta à API do Discord para enviar a mensagem. A implementação atual usa a biblioteca httpx para fazer as requisições HTTP, mas a gente pode trocar por outra biblioteca ou serviço de mensagens no futuro se for necessário. O importante é que a ferramenta seja fácil de usar e que envie as mensagens de forma confiável.

import os
import httpx

from briefing_agent.tools.base import BaseTool


class DiscordSender(BaseTool):
    """Sends messages to a Discord channel via webhook or bot API."""

    BASE_URL = "https://discord.com/api/v10"

    def __init__(self) -> None:
        """Initialize with bot token from environment variables."""
        self._token = os.getenv("DISCORD_BOT_TOKEN", "")

    def run(self, channel_id: str, content: str) -> None:
        """Send a message to the specified Discord channel."""
        chunks = self._split_message(content)
        for chunk in chunks:
            self._post(channel_id, chunk)

    def _split_message(self, content: str, limit: int = 2000) -> list[str]:
        """Split long messages into chunks within Discord's limit."""
        return [content[i:i + limit] for i in range(0, len(content), limit)]

    def _post(self, channel_id: str, content: str) -> None:
        """Send a single message chunk to Discord API."""
        url = f"{self.BASE_URL}/channels/{channel_id}/messages"
        headers = {"Authorization": f"Bot {self._token}"}
        httpx.post(url, json={"content": content}, headers=headers, timeout=10)