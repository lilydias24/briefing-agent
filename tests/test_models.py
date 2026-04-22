import pytest
from datetime import datetime
from briefing_agent.models.preferences import TopicPreference, UserPreferences
from briefing_agent.models.briefing import Article, TopicBriefing, Briefing

def test_topic_preference():
    topic = TopicPreference(name="Tech", keywords=["AI"], max_articles=5)
    assert topic.name == "Tech"

def test_user_preferences():
    prefs = UserPreferences(email="test@example.com")
    assert prefs.email == "test@example.com"

def test_article():
    article = Article(title="Test", summary="Summary", url="http://test.com", source="Source" )
    assert article.title == "Test"

def test_briefing():
    briefing = Briefing()
    assert isinstance(briefing.generated_at, datetime)
