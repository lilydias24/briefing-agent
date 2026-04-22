import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

from briefing_agent.tools.base import BaseTool

# Carrega .env
load_dotenv()


class EmailSender(BaseTool):
    """Sends the briefing content via email using SMTP."""

    def __init__(self) -> None:
        """Initialize SMTP credentials from environment variables."""
        self._host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self._port = int(os.getenv("SMTP_PORT", "587"))
        self._user = os.getenv("SMTP_USER", "")
        self._password = os.getenv("SMTP_PASSWORD", "")
        
        if not self._user or not self._password:
            print("⚠️  SMTP_USER ou SMTP_PASSWORD não configurados!")

    def run(self, recipient: str, subject: str, body: str) -> None:
        """Send an email with the given subject and body."""
        message = self._build_message(recipient, subject, body)
        self._send(message, recipient)

    def _build_message(self, recipient: str, subject: str, body: str) -> MIMEMultipart:
        """Construct the MIME email message."""
        message = MIMEMultipart()
        message["From"] = self._user
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))
        return message

    def _send(self, message: MIMEMultipart, recipient: str) -> None:
        """Connect to SMTP server and send the message."""
        try:
            with smtplib.SMTP(self._host, self._port) as server:
                server.starttls()
                server.login(self._user, self._password)
                server.sendmail(self._user, recipient, message.as_string())
                print(f"✅ Email enviado para {recipient}")
        except Exception as e:
            print(f"❌ Erro ao enviar email: {e}")
