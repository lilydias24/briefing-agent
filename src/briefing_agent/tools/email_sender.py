import html
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from briefing_agent.tools.base import BaseTool


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
        """Construct a multipart/alternative MIME message."""
        message = MIMEMultipart("alternative")
        message["From"] = self._user
        message["To"] = recipient
        message["Subject"] = subject
        message["Content-Language"] = "pt-BR"
        message.attach(MIMEText(body, "plain", "utf-8"))
        message.attach(MIMEText(self._build_html_body(subject, body), "html", "utf-8"))
        return message

    def _markdown_to_html(self, text: str) -> str:
        """Convert markdown-formatted plain text to HTML."""
        lines = text.split("\n")
        out: list[str] = []
        in_list = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("* ") or stripped.startswith("- "):
                if not in_list:
                    out.append('<ul style="margin:8px 0 12px 0;padding-left:22px;">')
                    in_list = True
                out.append(f"  <li>{self._fmt(stripped[2:])}</li>")
            else:
                if in_list:
                    out.append("</ul>")
                    in_list = False

                if not stripped:
                    out.append('<div style="height:6px;"></div>')
                else:
                    formatted = self._fmt(stripped)
                    if re.match(r"^<b>.*</b>:?$", formatted):
                        out.append(
                            '<p style="font-size:15px;font-weight:700;'
                            f'color:#111827;margin:18px 0 4px 0;">{formatted}</p>'
                        )
                    else:
                        out.append(f'<p style="margin:0 0 10px 0;">{formatted}</p>')

        if in_list:
            out.append("</ul>")

        return "\n".join(out)

    def _fmt(self, text: str) -> str:
        """Escape HTML entities, then convert **bold** and URLs to HTML tags."""
        text = html.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(
            # The text is already escaped, so the URL ends at whitespace or at an
            # escaped <, > or " entity (matched as whole entities, not characters).
            r"(https?://(?:(?!&lt;|&gt;|&quot;)\S)+)",
            r'<a href="\1" style="color:#4f46e5;">\1</a>',
            text,
        )
        return text

    def _build_html_body(self, subject: str, body: str) -> str:
        """Wrap the converted briefing in a styled HTML email template."""
        content = self._markdown_to_html(body)
        safe_subject = html.escape(subject)
        return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{safe_subject}</title>
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" bgcolor="#f3f4f6" style="padding:32px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;">
<tr><td bgcolor="#4f46e5" style="padding:30px 36px;text-align:center;border-radius:10px 10px 0 0;">
<p style="margin:0 0 6px 0;color:#c7d2fe;font-size:11px;letter-spacing:2px;text-transform:uppercase;font-family:Arial,sans-serif;">Briefing Di&aacute;rio</p>
<h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:bold;font-family:Arial,sans-serif;">{safe_subject}</h1>
</td></tr>
<tr><td bgcolor="#ffffff" style="padding:32px 36px;border-left:1px solid #e5e7eb;border-right:1px solid #e5e7eb;">
<div style="color:#374151;font-size:15px;line-height:1.75;font-family:Arial,sans-serif;">
{content}
</div>
</td></tr>
<tr><td bgcolor="#f9fafb" style="padding:16px 36px;text-align:center;border:1px solid #e5e7eb;border-top:none;border-radius:0 0 10px 10px;">
<p style="margin:0;color:#9ca3af;font-size:12px;font-family:Arial,sans-serif;">Gerado automaticamente pelo <b>Briefing Agent</b> &bull; N&atilde;o responda este email.</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""

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
