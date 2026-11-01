"""Search and trend analytics for the pipeline's normalized article dictionaries."""
from __future__ import annotations

import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _document_text(article: dict[str, Any]) -> str:
    entities = article.get("entities", []) or []
    if entities and isinstance(entities[0], dict):
        entity_text = " ".join(str(item.get("text", "")) for item in entities)
    else:
        entity_text = " ".join(str(item) for item in entities)
    return " ".join(str(value or "") for value in (
        article.get("title"), article.get("brief_summary", article.get("summary")),
        article.get("source"), article.get("topic"), entity_text
    )).strip()


class NewsSearch:
    """Rank stories with optional multilingual embeddings and a no-download TF-IDF fallback.

    Set NEWSINTEL_SEARCH_MODEL to a sentence-transformers model ID to opt in. The
    default remains lightweight lexical retrieval, not a claim of semantic search.
    """
    def __init__(self, model_name: str | None = None):
        self.model_name = (os.getenv("NEWSINTEL_SEARCH_MODEL", "") if model_name is None else model_name).strip()
        self.backend = "TF-IDF lexical similarity"
        self.warning = ""
        self._model = None

    def rank(self, query: str, articles: list[dict[str, Any]], limit: int = 60) -> list[tuple[dict[str, Any], float]]:
        self.warning = ""
        if not query.strip() or not articles:
            return []
        texts = [_document_text(article) for article in articles]
        try:
            scores = self._embedding_scores(query, texts) if self.model_name else None
            if scores is None:
                vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=12000,
                                             sublinear_tf=True, strip_accents="unicode")
                matrix = vectorizer.fit_transform(texts + [query])
                scores = cosine_similarity(matrix[-1], matrix[:-1])[0]
                self.backend = "TF-IDF lexical similarity"
        except ValueError:
            return []
        ranked = sorted(zip(articles, scores), key=lambda item: float(item[1]), reverse=True)
        return [(article, float(score)) for article, score in ranked[:max(1, limit)] if float(score) > 0]

    def _embedding_scores(self, query: str, texts: list[str]):
        try:
            from sentence_transformers import SentenceTransformer
            if self._model is None:
                self._model = SentenceTransformer(self.model_name)
            query_vector = self._model.encode(["query: " + query], normalize_embeddings=True)
            doc_vectors = self._model.encode(["passage: " + text for text in texts], normalize_embeddings=True)
            self.backend = f"Sentence-transformer embeddings ({self.model_name})"
            return cosine_similarity(query_vector, doc_vectors)[0]
        except Exception as exc:  # noqa: BLE001 - any optional model failure must fall back to local TF-IDF.
            self.warning = f"Embedding model unavailable ({type(exc).__name__}); fell back to TF-IDF."
            self.backend = "TF-IDF lexical similarity"
            return None


def topic_trends(articles: list[dict[str, Any]], window_days: int = 7,
                 now: datetime | None = None) -> list[dict[str, Any]]:
    """Compare topic volume in two adjacent windows; counts are descriptive, not forecasts."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    current_start = now - timedelta(days=window_days)
    previous_start = now - timedelta(days=2 * window_days)
    current: Counter[str] = Counter()
    previous: Counter[str] = Counter()
    for article in articles:
        topic = str(article.get("topic", "general"))
        if topic in {"general", "unclassified", "Other"}:
            continue
        raw = str(article.get("published", ""))
        try:
            published = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if published.tzinfo is None:
                published = published.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if current_start <= published <= now:
            current[topic] += 1
        elif previous_start <= published < current_start:
            previous[topic] += 1
    rows: list[dict[str, Any]] = []
    topics = sorted(current.keys() | previous.keys(), key=lambda topic: (-current[topic], topic))
    for topic in topics:
        count = current[topic]
        old = previous[topic]
        change = (100.0 if count else 0.0) if old == 0 else ((count - old) / old) * 100.0
        rows.append({"topic": topic, "current_count": count, "previous_count": old,
                     "change_pct": round(change, 1), "window_days": window_days})
    return rows
