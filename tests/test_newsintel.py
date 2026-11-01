from __future__ import annotations

import json
from pathlib import Path

from newsintel.analysis import analyze_articles, classify_topic, cluster_stories, make_brief, sentiment
from newsintel.models import FeedSource
from newsintel.rss import canonicalize_url, clean_feed_text, parse_feed_content
from newsintel.storage import load_cache, save_cache

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "sample_feed.xml"


def test_feed_parser_normalizes_attributed_metadata_and_removes_tracking_query():
    source = FeedSource("Fixture source", "https://example.test/feed", "https://example.test", "en", "ethiopia", "Fixture attribution")
    articles = parse_feed_content(source, FIXTURE.read_bytes())
    assert len(articles) == 3
    first = articles[0]
    assert first.title.startswith("Prime Minister Abiy Ahmed")
    assert first.url == "https://news.example.test/story-1"
    assert first.attribution == "Fixture attribution"
    assert first.region == "ethiopia"
    assert "<p>" not in first.summary
    assert first.published == "2026-11-01T09:00:00Z"


def test_feed_parser_skips_missing_title_or_unsafe_link():
    xml = b'<rss version="2.0"><channel><item><title>Bad URL</title><link>javascript:alert(1)</link></item><item><link>https://example.test/x</link></item></channel></rss>'
    source = FeedSource("X", "https://x.test/feed", "https://x.test")
    assert parse_feed_content(source, xml) == []
    assert canonicalize_url("javascript:alert(1)") == ""


def test_feed_text_and_url_cleaners():
    assert clean_feed_text("<p>Hello&nbsp; <b>world</b></p>") == "Hello world"
    assert canonicalize_url("HTTPS://Example.com/a?utm_medium=x&keep=1#frag") == "https://example.com/a?keep=1"


def test_topic_rule_and_evidence_not_probability():
    topic, share, method = classify_topic("The government passed a new climate policy in parliament")
    assert topic == "politics"
    assert 0 < share <= 1
    assert method == "keyword-rules-v1"
    assert classify_topic("A quiet day with no keywords")[0] == "general"


def test_sentiment_english_and_amharic_guard():
    assert sentiment("This is a wonderful breakthrough and a great result.", "en")["sentiment"] == "positive"
    unsupported = sentiment("የአየር ንብረት ለውጥ", "am")
    assert unsupported["sentiment"] == "unsupported"
    assert unsupported["sentiment_score"] is None


def test_summary_is_extractively_bounded_and_has_title_fallback():
    assert make_brief("Fallback title", "") == "Fallback title"
    brief = make_brief("Headline", "First short sentence. Second short sentence. Third longer sentence.", 40)
    assert brief.endswith("…")
    assert len(brief) <= 40


def test_analyzer_adds_expected_fields_and_marks_amharic_unsupported():
    records = [
        {"id": "a", "title": "Government approves renewable energy plan", "summary": "A new energy policy was announced.", "language": "en", "source": "A", "region": "ethiopia"},
        {"id": "b", "title": "የአየር ንብረት ለውጥ", "summary": "", "language": "am", "source": "B", "region": "ethiopia"},
    ]
    result = analyze_articles(records)
    assert result[0]["topic"] in {"politics", "climate", "general"}
    assert result[0]["brief_summary"]
    assert "entities" in result[0]
    assert result[1]["sentiment"] == "unsupported"
    assert result[1]["topic"] == "unclassified"
    assert result[1]["topic_method"] == "not-run-amharic-not-validated"
    assert result[1]["entities"] == []


def test_tfidf_groups_near_duplicates_but_not_unrelated_story():
    articles = [
        {"id": "1", "title": "Ethiopia announces a new renewable energy and climate policy", "summary": "Officials announce a clean energy programme."},
        {"id": "2", "title": "Ethiopia announces new climate and renewable energy policy", "summary": "A clean energy programme is announced by officials."},
        {"id": "3", "title": "Olympic marathon champion wins gold medal", "summary": "The athlete wins a close race."},
    ]
    grouped = cluster_stories(articles, threshold=0.34)
    assert grouped[0]["cluster_id"] == grouped[1]["cluster_id"] != ""
    assert grouped[0]["cluster_size"] == 2
    assert grouped[2]["cluster_id"] == ""
    assert cluster_stories([{"id": "x", "title": "a the and", "summary": "of an"}, {"id": "y", "title": "the and", "summary": "a"}])[0]["cluster_id"] == ""


def test_cache_round_trip_and_schema_validation(tmp_path):
    path = tmp_path / "cache.json"
    records = [{"id": "a", "title": "News"}]
    save_cache(path, records)
    assert load_cache(path) == records
    path.write_text(json.dumps({"schema_version": 999, "articles": []}), encoding="utf-8")
    try:
        load_cache(path)
    except ValueError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("Unsupported cache schema should fail closed")
