from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from briefing_agent.agents.setup_agent import (
    ERR_INVALID_EMAIL,
    ERR_NO_TOPICS,
    ERR_NOT_A_NUMBER,
    ERR_NUMBER_TOO_SMALL,
    QUESTIONS,
    SetupAgent,
)
from briefing_agent.models.preferences import UserPreferences


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent(storage: MagicMock | None = None) -> SetupAgent:
    """Return a SetupAgent wired to a mock storage."""
    if storage is None:
        storage = MagicMock()
        storage.save = MagicMock()
    return SetupAgent(storage=storage)


def _run_happy_path(agent: SetupAgent, session_id: str = "user1") -> str:
    """Drive the agent through the full 7-message happy path and return the final response."""
    agent.run("hi", session_id)
    agent.run("technology, energy", session_id)
    agent.run("AI, smart grid", session_id)
    agent.run("5", session_id)
    agent.run("user@example.com", session_id)
    agent.run("123456789", session_id)
    return agent.run("07:00", session_id)


def _run_from_step1(agent: SetupAgent, session_id: str = "user1") -> str:
    """Complete the flow starting at step 1 (e.g. right after a reset)."""
    agent.run("technology", session_id)
    agent.run("AI", session_id)
    agent.run("5", session_id)
    agent.run("user@example.com", session_id)
    agent.run("123456789", session_id)
    return agent.run("07:00", session_id)


def _reach_step(agent: SetupAgent, step: int, session_id: str = "u1") -> None:
    """Advance the agent session to a given step (1-based, where 1 = just started)."""
    messages = [
        "hi",
        "technology",
        "AI",
        "5",
        "user@example.com",
        "123456789",
    ]
    for msg in messages[:step]:
        agent.run(msg, session_id)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

class TestHappyPath:
    """Tests for the complete 6-step setup flow."""

    def test_complete_flow_calls_storage_save(self) -> None:
        """Completing all steps calls storage.save exactly once."""
        storage = MagicMock()
        agent = _make_agent(storage)
        _run_happy_path(agent)
        storage.save.assert_called_once()

    def test_saved_preferences_have_correct_email(self) -> None:
        """The email provided at step 4 is persisted in UserPreferences."""
        storage = MagicMock()
        agent = _make_agent(storage)
        _run_happy_path(agent)
        saved: UserPreferences = storage.save.call_args[0][0]
        assert saved.email == "user@example.com"

    def test_saved_preferences_have_correct_discord_channel(self) -> None:
        """The Discord channel ID provided at step 5 is persisted in UserPreferences."""
        storage = MagicMock()
        agent = _make_agent(storage)
        _run_happy_path(agent)
        saved: UserPreferences = storage.save.call_args[0][0]
        assert saved.discord_channel_id == "123456789"

    def test_saved_preferences_have_correct_topic_names(self) -> None:
        """Both topic names provided at step 1 appear in the saved preferences."""
        storage = MagicMock()
        agent = _make_agent(storage)
        _run_happy_path(agent)
        saved: UserPreferences = storage.save.call_args[0][0]
        topic_names = [t.name for t in saved.topics]
        assert "technology" in topic_names
        assert "energy" in topic_names

    def test_saved_preferences_have_correct_schedule(self) -> None:
        """The schedule time provided at step 6 is persisted in UserPreferences."""
        storage = MagicMock()
        agent = _make_agent(storage)
        _run_happy_path(agent)
        saved: UserPreferences = storage.save.call_args[0][0]
        assert saved.schedule_hour == 7
        assert saved.schedule_minute == 0

    def test_confirmation_contains_email(self) -> None:
        """The confirmation message includes the configured email address."""
        agent = _make_agent()
        result = _run_happy_path(agent)
        assert "user@example.com" in result

    def test_confirmation_contains_discord_channel(self) -> None:
        """The confirmation message includes the configured Discord channel ID."""
        agent = _make_agent()
        result = _run_happy_path(agent)
        assert "123456789" in result

    def test_session_cleared_after_completion(self) -> None:
        """After completion the session is deleted; the next message starts a fresh flow."""
        agent = _make_agent()
        _run_happy_path(agent, session_id="u1")
        response = agent.run("hi", "u1")
        assert response == QUESTIONS[1]

    def test_step0_empty_message_returns_first_question(self) -> None:
        """An empty message on a new session returns the first setup question."""
        agent = _make_agent()
        response = agent.run("", "new_user")
        assert response == QUESTIONS[1]

    def test_step0_any_message_returns_first_question(self) -> None:
        """Any non-reset message on a new session returns the first setup question."""
        agent = _make_agent()
        response = agent.run("hello there", "u1")
        assert response == QUESTIONS[1]

    def test_step1_returns_second_question(self) -> None:
        """A valid topics input at step 1 advances the session to step 2."""
        agent = _make_agent()
        agent.run("hi", "u1")
        response = agent.run("technology", "u1")
        assert response == QUESTIONS[2]

    def test_step2_returns_third_question(self) -> None:
        """A keywords input at step 2 advances the session to step 3."""
        agent = _make_agent()
        _reach_step(agent, 2)
        response = agent.run("AI", "u1")
        assert response == QUESTIONS[3]

    def test_step3_returns_fourth_question(self) -> None:
        """A valid integer at step 3 advances the session to step 4."""
        agent = _make_agent()
        _reach_step(agent, 3)
        response = agent.run("5", "u1")
        assert response == QUESTIONS[4]

    def test_step4_returns_fifth_question(self) -> None:
        """A valid email at step 4 advances the session to step 5."""
        agent = _make_agent()
        _reach_step(agent, 4)
        response = agent.run("user@example.com", "u1")
        assert response == QUESTIONS[5]

    def test_step5_returns_sixth_question(self) -> None:
        """Any non-empty input at step 5 advances the session to step 6."""
        agent = _make_agent()
        _reach_step(agent, 5)
        response = agent.run("123456789", "u1")
        assert response == QUESTIONS[6]


# ---------------------------------------------------------------------------
# Reset / restart / cancel
# ---------------------------------------------------------------------------

class TestReset:
    """Tests for reset commands that restart the setup flow from step 1."""

    def test_reset_at_step1_returns_first_question(self) -> None:
        """'reset' at step 1 restarts the session and returns the first question."""
        agent = _make_agent()
        agent.run("hi", "u1")
        response = agent.run("reset", "u1")
        assert response == QUESTIONS[1]

    def test_restart_at_step3_returns_first_question(self) -> None:
        """'restart' mid-flow restarts the session and returns the first question."""
        agent = _make_agent()
        _reach_step(agent, 3)
        response = agent.run("restart", "u1")
        assert response == QUESTIONS[1]

    def test_cancel_at_step5_returns_first_question(self) -> None:
        """'cancel' late in the flow restarts the session and returns the first question."""
        agent = _make_agent()
        _reach_step(agent, 5)
        response = agent.run("cancel", "u1")
        assert response == QUESTIONS[1]

    def test_reset_is_case_insensitive(self) -> None:
        """Reset commands are matched case-insensitively."""
        agent = _make_agent()
        agent.run("hi", "u1")
        response = agent.run("RESET", "u1")
        assert response == QUESTIONS[1]

    def test_restart_is_case_insensitive(self) -> None:
        """'RESTART' in uppercase triggers a reset just like lowercase 'restart'."""
        agent = _make_agent()
        agent.run("hi", "u1")
        response = agent.run("RESTART", "u1")
        assert response == QUESTIONS[1]

    def test_cancel_is_case_insensitive(self) -> None:
        """'CANCEL' in uppercase triggers a reset just like lowercase 'cancel'."""
        agent = _make_agent()
        agent.run("hi", "u1")
        response = agent.run("CANCEL", "u1")
        assert response == QUESTIONS[1]

    def test_after_reset_flow_can_be_completed(self) -> None:
        """After a reset the user can complete the full flow and save preferences."""
        storage = MagicMock()
        agent = _make_agent(storage)
        agent.run("hi", "u1")
        agent.run("reset", "u1")
        _run_from_step1(agent, "u1")
        storage.save.assert_called_once()

    def test_reset_does_not_call_save(self) -> None:
        """Issuing a reset command does not persist any preferences."""
        storage = MagicMock()
        agent = _make_agent(storage)
        _reach_step(agent, 5)
        agent.run("reset", "u1")
        storage.save.assert_not_called()


# ---------------------------------------------------------------------------
# Invalid e-mail (step 4)
# ---------------------------------------------------------------------------

class TestInvalidEmail:
    """Tests for invalid e-mail inputs at step 4."""

    def test_plain_text_returns_error(self) -> None:
        """Input with no '@' returns the invalid-email error message."""
        agent = _make_agent()
        _reach_step(agent, 4)
        response = agent.run("not-an-email", "u1")
        assert response == ERR_INVALID_EMAIL

    def test_missing_at_returns_error(self) -> None:
        """Input without the '@' character returns the invalid-email error message."""
        agent = _make_agent()
        _reach_step(agent, 4)
        response = agent.run("userexample.com", "u1")
        assert response == ERR_INVALID_EMAIL

    def test_invalid_email_does_not_advance_step(self) -> None:
        """An invalid e-mail keeps the session at step 4; a valid one then advances it."""
        agent = _make_agent()
        _reach_step(agent, 4)
        agent.run("not-an-email", "u1")
        response = agent.run("valid@example.com", "u1")
        assert response == QUESTIONS[5]

    def test_invalid_email_does_not_call_save(self) -> None:
        """An invalid e-mail input does not trigger a storage save."""
        storage = MagicMock()
        agent = _make_agent(storage)
        _reach_step(agent, 4)
        agent.run("not-an-email", "u1")
        storage.save.assert_not_called()

    def test_email_embedded_in_sentence_is_accepted(self) -> None:
        """A valid e-mail embedded in a longer sentence is extracted and accepted."""
        agent = _make_agent()
        _reach_step(agent, 4)
        response = agent.run("my email is test@mail.com thanks", "u1")
        assert response == QUESTIONS[5]

    def test_multiple_invalid_attempts_then_valid(self) -> None:
        """The session remains at step 4 across multiple invalid attempts."""
        agent = _make_agent()
        _reach_step(agent, 4)
        agent.run("nope", "u1")
        agent.run("still-nope", "u1")
        response = agent.run("ok@email.com", "u1")
        assert response == QUESTIONS[5]


# ---------------------------------------------------------------------------
# Invalid max_articles (step 3)
# ---------------------------------------------------------------------------

class TestInvalidMaxArticles:
    """Tests for invalid max_articles inputs at step 3."""

    def test_non_numeric_returns_error(self) -> None:
        """A string with no digits returns the not-a-number error message."""
        agent = _make_agent()
        _reach_step(agent, 3)
        response = agent.run("abc", "u1")
        assert response == ERR_NOT_A_NUMBER

    def test_zero_returns_error(self) -> None:
        """The value '0' returns the too-small error message."""
        agent = _make_agent()
        _reach_step(agent, 3)
        response = agent.run("0", "u1")
        assert response == ERR_NUMBER_TOO_SMALL

    def test_invalid_does_not_advance_step(self) -> None:
        """An invalid value keeps the session at step 3; a valid one then advances it."""
        agent = _make_agent()
        _reach_step(agent, 3)
        agent.run("abc", "u1")
        response = agent.run("5", "u1")
        assert response == QUESTIONS[4]

    def test_valid_number_advances_to_step4(self) -> None:
        """A positive integer at step 3 advances the session to step 4."""
        agent = _make_agent()
        _reach_step(agent, 3)
        response = agent.run("10", "u1")
        assert response == QUESTIONS[4]

    def test_multiple_invalid_attempts_then_valid(self) -> None:
        """The session remains at step 3 across multiple invalid attempts."""
        agent = _make_agent()
        _reach_step(agent, 3)
        agent.run("abc", "u1")
        agent.run("0", "u1")
        response = agent.run("3", "u1")
        assert response == QUESTIONS[4]

    def test_max_articles_value_is_saved(self) -> None:
        """The max_articles value entered at step 3 is applied to all topics."""
        storage = MagicMock()
        agent = _make_agent(storage)
        _reach_step(agent, 3)
        agent.run("7", "u1")
        agent.run("user@example.com", "u1")
        agent.run("123456", "u1")
        agent.run("08:00", "u1")
        saved: UserPreferences = storage.save.call_args[0][0]
        assert all(t.max_articles == 7 for t in saved.topics)


# ---------------------------------------------------------------------------
# Invalid topics (step 1)
# ---------------------------------------------------------------------------

class TestInvalidTopics:
    """Tests for invalid topics inputs at step 1."""

    def test_empty_csv_returns_error(self) -> None:
        """A string of only commas yields no topics and returns the error message."""
        agent = _make_agent()
        agent.run("hi", "u1")
        response = agent.run(",,,", "u1")
        assert response == ERR_NO_TOPICS

    def test_whitespace_only_re_prompts_current_question(self) -> None:
        """A whitespace-only message is treated as empty and re-prompts the current step."""
        agent = _make_agent()
        agent.run("hi", "u1")
        response = agent.run("   ", "u1")
        assert response == QUESTIONS[1]

    def test_invalid_topics_does_not_advance_step(self) -> None:
        """An invalid topics input keeps the session at step 1; a valid one advances it."""
        agent = _make_agent()
        agent.run("hi", "u1")
        agent.run(",,,", "u1")
        response = agent.run("technology", "u1")
        assert response == QUESTIONS[2]


# ---------------------------------------------------------------------------
# Multiple independent sessions
# ---------------------------------------------------------------------------

class TestMultipleSessions:
    """Tests verifying that concurrent sessions for different users are isolated."""

    def test_sessions_are_isolated(self) -> None:
        """A new session is independent of any other session in progress."""
        agent = _make_agent()
        agent.run("hi", "user_a")
        agent.run("technology", "user_a")

        response_b = agent.run("hi", "user_b")
        assert response_b == QUESTIONS[1]

    def test_two_sessions_save_independently(self) -> None:
        """Completing two sessions calls storage.save twice, once per session."""
        storage = MagicMock()
        agent = _make_agent(storage)
        _run_happy_path(agent, "user_a")
        _run_happy_path(agent, "user_b")
        assert storage.save.call_count == 2

    def test_completing_one_session_does_not_affect_other(self) -> None:
        """Completing user_b's session does not change user_a's current step."""
        agent = _make_agent()
        _reach_step(agent, 3, session_id="user_a")
        _run_happy_path(agent, "user_b")

        response = agent.run("5", "user_a")
        assert response == QUESTIONS[4]
