# Briefing Agent

A system that automatically generates personalized news briefings and distributes them via Discord and email using AI agents.

## How it works

The user configures their preferences entirely through a Discord conversation with the bot (topics of interest, keywords, email address, delivery time). At the configured time every day, the agent fetches recent news from NewsAPI, formats a consolidated briefing using a Groq LLM, and delivers it to the configured Discord channel and email address.

## Requirements

- Python 3.11+
- A [NewsAPI](https://newsapi.org) key
- A Discord bot token
- An SMTP-enabled email account (e.g. Gmail with an App Password)
- A [Groq](https://console.groq.com) API key

## Installation

### Option 1 — uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager. If you don't have it installed:

```bash
pip install uv
```

Then set up the project:

```bash
# 1. Clone the repository
git clone <repository-url>
cd grupo-17

# 2. Create a virtual environment and install dependencies
uv sync

# 3. Activate the virtual environment
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate
```

### Option 2 — pip

```bash
# 1. Clone the repository
git clone <repository-url>
cd grupo-17

# 2. Install the package and development dependencies
pip install -e ".[dev]"
```

## Configuration

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```
NEWS_API_KEY=your_newsapi_key
DISCORD_BOT_TOKEN=your_discord_bot_token
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
GROQ_API_KEY=your_groq_api_key
```

> **Gmail users:** generate an [App Password](https://myaccount.google.com/apppasswords) instead of using your account password.

## Running

```bash
python -m briefing_agent.main
```

The process starts two concurrent components:
- **Discord bot** — listens for messages and guides users through the 6-step preference setup.
- **Scheduler** — runs the briefing pipeline daily at the time configured by the user (default: 07:00).

### First-time setup via Discord

Send any message to the bot in a server where it is present. It will guide you through:

1. Topics of interest (e.g. `technology, energy, cybersecurity`)
2. Keywords per topic (e.g. `AI, smart grid, ransomware`)
3. Maximum number of articles per topic (e.g. `5`)
4. Destination email address
5. Discord channel ID for delivery
6. Delivery time in HH:MM format (e.g. `07:00`)

Type `reset`, `restart`, or `cancel` at any point to start over.

## Running the tests

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_models.py -v
pytest tests/test_setup_agent.py -v
pytest tests/test_news_fetcher.py -v
pytest tests/test_tools.py -v
pytest tests/test_storage.py -v
```

To run all tests:

```bash
python -m pytest -v
```

## Project structure

```
grupo-17/
├── .env.example              # Environment variable template
├── .gitignore
├── pyproject.toml            # Project metadata and dependencies
├── pytest.ini                # pytest configuration
├── README.md
├── src/
│   └── briefing_agent/
│       ├── main.py           # Application entry point
│       ├── bot.py            # Discord bot
│       ├── agents/
│       │   ├── base.py       # Abstract base class for agents
│       │   ├── briefing_agent.py  # Fetches news, formats and delivers briefing
│       │   └── setup_agent.py     # Collects user preferences via Discord chat
│       ├── models/
│       │   ├── briefing.py   # Article, TopicBriefing, Briefing dataclasses
│       │   └── preferences.py     # TopicPreference, UserPreferences dataclasses
│       ├── tools/
│       │   ├── base.py       # Abstract base class for tools
│       │   ├── discord_sender.py  # Posts messages to Discord via API
│       │   ├── email_sender.py    # Sends emails via SMTP
│       │   └── news_fetcher.py    # Fetches articles from NewsAPI
│       ├── storage/
│       │   ├── base.py       # Abstract base class for storage
│       │   └── json_storage.py    # Persists preferences and briefings as JSON
│       └── scheduler/
│           ├── base.py       # Abstract base class for schedulers
│           └── briefing_scheduler.py  # APScheduler-based daily runner
└── tests/
    ├── conftest.py           # Shared fixtures and test doubles
    ├── test_models.py        # Unit tests for data models
    ├── test_news_fetcher.py  # Unit tests for NewsFetcher (mocked HTTP)
    ├── test_setup_agent.py   # Unit tests for SetupAgent flow
    ├── test_storage.py       # Unit tests for JsonStorage
    └── test_tools.py         # Unit tests for EmailSender and DiscordSender
```

## Dependencies

| Package | Purpose |
|---|---|
| `agno` | AI agent framework (Groq integration) |
| `discord.py` | Discord bot library |
| `apscheduler` | Daily briefing scheduler |
| `httpx` | HTTP client for NewsAPI and Discord API |
| `python-dotenv` | Loads environment variables from `.env` |
| `groq` | Groq LLM client |
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support |
| `ruff` | Linter and formatter |

## My contribution

- Test suite for the models (including edge cases), the full `SetupAgent` flow and
  the `NewsFetcher` query building and article parsing, plus the pytest setup.
- HTML formatting for the briefing email, including its Portuguese subject and header title.

## About this repository

Group project for the LPESI course at UNIPAMPA (2026/1). This is a copy, with full
history, of the group's original GitLab repository. Contributor emails were anonymized
in the history.