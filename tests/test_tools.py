from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from briefing_agent.tools.discord_sender import DiscordSender
from briefing_agent.tools.email_sender import EmailSender


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SMTP_PATCH = "briefing_agent.tools.email_sender.smtplib.SMTP"
_HTTPX_POST_PATCH = "briefing_agent.tools.discord_sender.httpx.post"


def _make_email_sender(monkeypatch: pytest.MonkeyPatch) -> EmailSender:
    """Return an EmailSender with SMTP credentials set via environment variables."""
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    return EmailSender()


def _make_discord_sender(monkeypatch: pytest.MonkeyPatch) -> DiscordSender:
    """Return a DiscordSender with a bot token set via environment variable."""
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "test-bot-token")
    return DiscordSender()


def _mock_smtp_server(mock_smtp_class: MagicMock) -> MagicMock:
    """Extract the mock server instance from a patched smtplib.SMTP class."""
    return mock_smtp_class.return_value.__enter__.return_value


def _make_http_response(status_code: int = 200) -> MagicMock:
    """Return a mock httpx response that does not raise on raise_for_status."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.status_code = status_code
    return mock_resp


# ---------------------------------------------------------------------------
# EmailSender
# ---------------------------------------------------------------------------

class TestEmailSenderBuildMessage:
    """Tests for EmailSender._build_message."""

    def test_from_field_uses_smtp_user(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The 'From' header is set to the configured SMTP_USER."""
        sender = _make_email_sender(monkeypatch)
        msg = sender._build_message("to@example.com", "Subject", "Body")
        assert msg["From"] == "sender@example.com"

    def test_to_field_matches_recipient(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The 'To' header is set to the provided recipient address."""
        sender = _make_email_sender(monkeypatch)
        msg = sender._build_message("recipient@example.com", "Subject", "Body")
        assert msg["To"] == "recipient@example.com"

    def test_subject_field_preserved(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The 'Subject' header is set to the provided subject string."""
        sender = _make_email_sender(monkeypatch)
        msg = sender._build_message("to@example.com", "My Subject", "Body")
        assert msg["Subject"] == "My Subject"

    def test_body_is_attached_as_plain_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The email body is attached as a plain-text MIME part."""
        sender = _make_email_sender(monkeypatch)
        msg = sender._build_message("to@example.com", "Subject", "Hello world")
        payload = msg.get_payload()
        assert len(payload) == 1
        assert payload[0].get_content_type() == "text/plain"
        assert "Hello world" in payload[0].get_payload()


class TestEmailSenderSend:
    """Tests for the SMTP interaction performed by EmailSender._send and run()."""

    def test_smtp_server_instantiated_with_host_and_port(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """smtplib.SMTP is called with the configured host and port."""
        sender = _make_email_sender(monkeypatch)
        with patch(_SMTP_PATCH) as mock_smtp_class:
            _mock_smtp_server(mock_smtp_class)
            sender.run("to@example.com", "Subject", "Body")
        mock_smtp_class.assert_called_once_with("smtp.example.com", 587)

    def test_starttls_is_called(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """server.starttls() is called to upgrade the connection to TLS."""
        sender = _make_email_sender(monkeypatch)
        with patch(_SMTP_PATCH) as mock_smtp_class:
            server = _mock_smtp_server(mock_smtp_class)
            sender.run("to@example.com", "Subject", "Body")
        server.starttls.assert_called_once()

    def test_login_called_with_user_and_password(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """server.login() is called with the SMTP_USER and SMTP_PASSWORD credentials."""
        sender = _make_email_sender(monkeypatch)
        with patch(_SMTP_PATCH) as mock_smtp_class:
            server = _mock_smtp_server(mock_smtp_class)
            sender.run("to@example.com", "Subject", "Body")
        server.login.assert_called_once_with("sender@example.com", "secret")

    def test_sendmail_called_with_correct_sender_and_recipient(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """server.sendmail() is called with SMTP_USER as sender and the given recipient."""
        sender = _make_email_sender(monkeypatch)
        with patch(_SMTP_PATCH) as mock_smtp_class:
            server = _mock_smtp_server(mock_smtp_class)
            sender.run("to@example.com", "Subject", "Body")
        call_args = server.sendmail.call_args
        assert call_args[0][0] == "sender@example.com"
        assert call_args[0][1] == "to@example.com"

    def test_sendmail_message_contains_subject(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The raw message string passed to sendmail contains the subject line."""
        sender = _make_email_sender(monkeypatch)
        with patch(_SMTP_PATCH) as mock_smtp_class:
            server = _mock_smtp_server(mock_smtp_class)
            sender.run("to@example.com", "Unique Subject XYZ", "Body")
        raw_message: str = server.sendmail.call_args[0][2]
        assert "Unique Subject XYZ" in raw_message

    def test_smtp_exception_is_caught_and_not_raised(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An SMTP error during send does not propagate as an unhandled exception."""
        sender = _make_email_sender(monkeypatch)
        with patch(_SMTP_PATCH) as mock_smtp_class:
            server = _mock_smtp_server(mock_smtp_class)
            server.starttls.side_effect = Exception("Connection refused")
            sender.run("to@example.com", "Subject", "Body")

    def test_run_completes_without_error_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """run() returns None and does not raise when the SMTP interaction succeeds."""
        sender = _make_email_sender(monkeypatch)
        with patch(_SMTP_PATCH) as mock_smtp_class:
            _mock_smtp_server(mock_smtp_class)
            result = sender.run("to@example.com", "Subject", "Body")
        assert result is None


# ---------------------------------------------------------------------------
# DiscordSender — message splitting
# ---------------------------------------------------------------------------

class TestDiscordSenderSplitMessage:
    """Tests for DiscordSender._split_message."""

    def test_short_message_is_single_chunk(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A message shorter than 2000 characters is returned as a single chunk."""
        sender = _make_discord_sender(monkeypatch)
        chunks = sender._split_message("hello")
        assert chunks == ["hello"]

    def test_exactly_2000_chars_is_single_chunk(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A message of exactly 2000 characters is not split."""
        sender = _make_discord_sender(monkeypatch)
        content = "x" * 2000
        chunks = sender._split_message(content)
        assert len(chunks) == 1
        assert len(chunks[0]) == 2000

    def test_2001_chars_is_split_into_two_chunks(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A message of 2001 characters is split into exactly two chunks."""
        sender = _make_discord_sender(monkeypatch)
        content = "x" * 2001
        chunks = sender._split_message(content)
        assert len(chunks) == 2

    def test_2001_chars_first_chunk_has_2000(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The first chunk of a 2001-character split contains exactly 2000 characters."""
        sender = _make_discord_sender(monkeypatch)
        content = "x" * 2001
        chunks = sender._split_message(content)
        assert len(chunks[0]) == 2000

    def test_2001_chars_second_chunk_has_remaining(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The second chunk of a 2001-character split contains the remaining 1 character."""
        sender = _make_discord_sender(monkeypatch)
        content = "x" * 2001
        chunks = sender._split_message(content)
        assert len(chunks[1]) == 1

    def test_content_is_preserved_across_chunks(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Joining all chunks reconstructs the original message exactly."""
        sender = _make_discord_sender(monkeypatch)
        content = "ab" * 1500
        chunks = sender._split_message(content)
        assert "".join(chunks) == content

    def test_empty_message_returns_empty_list(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty string produces an empty list of chunks."""
        sender = _make_discord_sender(monkeypatch)
        chunks = sender._split_message("")
        assert chunks == []


# ---------------------------------------------------------------------------
# DiscordSender — HTTP posts
# ---------------------------------------------------------------------------

class TestDiscordSenderPost:
    """Tests for the HTTP interaction performed by DiscordSender._post and run()."""

    def test_short_message_makes_one_http_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A message shorter than 2000 characters triggers exactly one POST request."""
        sender = _make_discord_sender(monkeypatch)
        with patch(_HTTPX_POST_PATCH, return_value=_make_http_response()) as mock_post:
            sender.run("123456", "short message")
        assert mock_post.call_count == 1

    def test_exactly_2000_chars_makes_one_http_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A message of exactly 2000 characters triggers exactly one POST request."""
        sender = _make_discord_sender(monkeypatch)
        with patch(_HTTPX_POST_PATCH, return_value=_make_http_response()) as mock_post:
            sender.run("123456", "x" * 2000)
        assert mock_post.call_count == 1

    def test_2001_chars_makes_two_http_calls(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A message of 2001 characters is split and triggers exactly two POST requests."""
        sender = _make_discord_sender(monkeypatch)
        with patch(_HTTPX_POST_PATCH, return_value=_make_http_response()) as mock_post:
            sender.run("123456", "x" * 2001)
        assert mock_post.call_count == 2

    def test_post_targets_correct_channel_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The POST request URL includes the provided channel ID."""
        sender = _make_discord_sender(monkeypatch)
        with patch(_HTTPX_POST_PATCH, return_value=_make_http_response()) as mock_post:
            sender.run("987654321", "hello")
        url: str = mock_post.call_args[0][0]
        assert "987654321" in url

    def test_post_sends_authorization_header(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The POST request includes a Bot authorization header."""
        sender = _make_discord_sender(monkeypatch)
        with patch(_HTTPX_POST_PATCH, return_value=_make_http_response()) as mock_post:
            sender.run("123456", "hello")
        headers: dict = mock_post.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bot test-bot-token"

    def test_post_sends_content_in_json_body(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The POST request JSON body includes the message content."""
        sender = _make_discord_sender(monkeypatch)
        with patch(_HTTPX_POST_PATCH, return_value=_make_http_response()) as mock_post:
            sender.run("123456", "hello discord")
        json_body: dict = mock_post.call_args.kwargs["json"]
        assert json_body["content"] == "hello discord"

    def test_post_calls_raise_for_status(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """raise_for_status() is called to surface HTTP error codes."""
        sender = _make_discord_sender(monkeypatch)
        mock_resp = _make_http_response()
        with patch(_HTTPX_POST_PATCH, return_value=mock_resp):
            sender.run("123456", "hello")
        mock_resp.raise_for_status.assert_called_once()

    def test_http_error_is_caught_and_not_raised(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An HTTP status error from Discord does not propagate as an unhandled exception."""
        import httpx

        sender = _make_discord_sender(monkeypatch)
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_resp
        )
        with patch(_HTTPX_POST_PATCH, return_value=mock_resp):
            sender.run("123456", "hello")

    def test_request_error_is_caught_and_not_raised(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A network-level request error does not propagate as an unhandled exception."""
        import httpx

        sender = _make_discord_sender(monkeypatch)
        with patch(
            _HTTPX_POST_PATCH,
            side_effect=httpx.RequestError("timeout", request=MagicMock()),
        ):
            sender.run("123456", "hello")
