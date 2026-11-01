from datetime import datetime, timezone

from newsintel.discovery import NewsSearch, rank_with_embedding_model, topic_trends


def test_tfidf_similarity_ranks_relevant_story_and_reports_backend():
    articles = [
        {"title": "Ethiopia drought and climate update", "brief_summary": "Dry conditions continue", "topic": "climate"},
        {"title": "Football final ends in a draw", "brief_summary": "The teams split points", "topic": "sports"},
    ]
    search = NewsSearch(model_name="")
    results = search.rank("climate drought", articles)
    assert results
    assert results[0][0]["topic"] == "climate"
    assert results[0][1] > 0
    assert search.backend == "TF-IDF lexical similarity"


def test_topic_trends_compare_adjacent_windows_without_forecast_claim():
    now = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
    articles = [
        {"topic": "climate", "published": "2026-11-01T09:00:00Z"},
        {"topic": "climate", "published": "2026-10-31T09:00:00Z"},
        {"topic": "climate", "published": "2026-10-20T09:00:00Z"},
        {"topic": "sports", "published": "2026-10-30T09:00:00Z"},
        {"topic": "business", "published": "2026-10-20T09:00:00Z"},
        {"topic": "general", "published": "2026-10-31T09:00:00Z"},
    ]
    rows = topic_trends(articles, window_days=7, now=now)
    climate = next(row for row in rows if row["topic"] == "climate")
    assert climate == {"topic": "climate", "current_count": 2, "previous_count": 1,
                       "change_pct": 100.0, "window_days": 7}
    assert all(row["topic"] != "general" for row in rows)
    assert next(row for row in rows if row["topic"] == "sports")["previous_count"] == 0
    business = next(row for row in rows if row["topic"] == "business")
    assert business["current_count"] == 0 and business["change_pct"] == -100.0


def test_similarity_search_handles_empty_query_and_articles():
    search = NewsSearch(model_name="")
    assert search.rank("", [{"title": "headline"}]) == []
    assert search.rank("headline", []) == []


def test_embedding_ranker_uses_e5_prefixes_and_ranks_relevant_document():
    class FakeModel:
        def __init__(self):
            self.inputs = []

        def encode(self, texts, **kwargs):
            self.inputs.append((list(texts), kwargs))
            if texts[0].startswith("query:"):
                return [[1.0, 0.0]]
            return [[1.0, 0.0] if "climate" in text.lower() else [0.0, 1.0] for text in texts]

    model = FakeModel()
    articles = [
        {"id": "climate", "title": "Drought and climate", "brief_summary": "Dry crops"},
        {"id": "sports", "title": "Football final", "brief_summary": "Teams split points"},
    ]
    ranked = rank_with_embedding_model("climate drought", articles, model, limit=2)

    assert ranked[0][0]["id"] == "climate"
    assert ranked[0][1] > ranked[1][1]
    assert model.inputs[0][0] == ["query: climate drought"]
    assert model.inputs[1][0][0].startswith("passage: ")
    assert all(call[1]["normalize_embeddings"] is True for call in model.inputs)
    assert rank_with_embedding_model("", articles, model) == []
