import app
from app import _matches, apply_filters, render_cards


def test_render_cards_escapes_feed_content_and_rejects_unsafe_links():
    markup = render_cards([{
        "title": "<script>alert('x')</script>",
        "url": "javascript:alert(1)",
        "summary": "<img src=x onerror=alert(1)>",
        "brief_summary": "<img src=x onerror=alert(1)>",
        "source": "<b>Publisher</b>",
        "attribution": "<b>Publisher</b>",
        "sentiment": "neutral",
        "topic": "general",
        "entities": [{"text": "<svg onload=alert(1)>", "label": "TEST"}],
    }])
    assert "<script>" not in markup
    assert "<img src=x" not in markup
    assert "<svg onload" not in markup
    assert 'href="javascript:' not in markup
    assert "&lt;script&gt;" in markup


def test_story_filters_cover_topic_sentiment_query_and_region():
    story = {"title": "Ethiopia climate update", "summary": "Drought", "source": "Local source", "topic": "climate", "sentiment": "negative", "region": "ethiopia", "entities": []}
    assert _matches(story, "climate", "Negative", "drought", True)
    assert not _matches(story, "politics", "Negative", "drought", True)
    assert not _matches(story, "climate", "Positive", "drought", True)
    assert not _matches(story, "climate", "Negative", "unmatched", True)
    assert _matches(story, "climate", "Negative", "drought", False)
    non_ethiopia = {**story, "region": "global"}
    assert not _matches(non_ethiopia, "climate", "Negative", "drought", True)


def test_similarity_mode_ranks_relevant_stories(monkeypatch):
    monkeypatch.setattr(app.SEARCH, "model_name", "")
    articles = [
        {"id": "1", "title": "Ethiopia drought and climate update", "summary": "Dry conditions continue", "brief_summary": "Dry conditions continue", "source": "A", "topic": "climate", "sentiment": "neutral", "region": "ethiopia", "entities": [], "url": "https://example.test/1"},
        {"id": "2", "title": "Football final ends in a draw", "summary": "The teams split points", "brief_summary": "The teams split points", "source": "B", "topic": "sports", "sentiment": "neutral", "region": "global", "entities": [], "url": "https://example.test/2"},
    ]
    markup, status = apply_filters(articles, "All topics", "All sentiment", "climate drought", False, "Similarity-ranked")
    assert "Ethiopia drought and climate update" in markup
    assert "Football final" not in markup
    assert "TF-IDF lexical similarity" in status
