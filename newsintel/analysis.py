from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "politics": ("government", "president", "minister", "parliament", "election", "policy", "vote", "diplomat", "political", "congress", "senate"),
    "business": ("business", "economy", "market", "company", "trade", "bank", "inflation", "investment", "jobs", "finance", "startup"),
    "technology": ("technology", "artificial intelligence", "ai", "software", "chip", "cyber", "internet", "robot", "digital", "computer"),
    "health": ("health", "hospital", "disease", "vaccine", "medical", "patient", "doctor", "outbreak", "medicine"),
    "climate": ("climate", "warming", "emissions", "weather", "flood", "drought", "wildfire", "carbon", "environment"),
    "science": ("science", "research", "scientist", "study", "space", "discovery", "experiment", "university"),
    "sports": ("sport", "football", "soccer", "athlete", "match", "tournament", "olympic", "championship", "goal"),
    "conflict": ("war", "conflict", "attack", "military", "troops", "ceasefire", "weapon", "armed", "violence", "security"),
    "world": ("world", "international", "global", "africa", "ethiopia", "addis ababa", "diplomacy", "border"),
}

VADER = SentimentIntensityAnalyzer()
_ETHIOPIC = re.compile(r"[\u1200-\u137f]")
_ENTITY_FALLBACK = re.compile(r"\b(?:[A-Z][a-z]+|[A-Z]{2,})(?:[ -](?:[A-Z][a-z]+|[A-Z]{2,}))*\b")
_NON_ENTITIES = {"The", "A", "An", "This", "That", "These", "Those", "After", "Before", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"}
_SPACY_NLP = None
_SPACY_ATTEMPTED = False


def classify_topic(text: str) -> tuple[str, float, str]:
    """Explainable rule-based English topic baseline; score is evidence, not probability."""
    normalized = f" {text.casefold()} "
    scores: Counter[str] = Counter()
    for topic, keywords in TOPIC_KEYWORDS.items():
        for keyword in keywords:
            count = len(re.findall(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", normalized))
            scores[topic] += count
    if not scores or max(scores.values()) == 0:
        return "general", 0.0, "keyword-rules-v1"
    topic, raw = scores.most_common(1)[0]
    total = sum(scores.values())
    return topic, round(raw / total, 3), "keyword-rules-v1"


def sentiment(text: str, language: str = "en") -> dict[str, Any]:
    if language.lower().startswith("am") or _ETHIOPIC.search(text):
        return {"sentiment": "unsupported", "sentiment_score": None, "sentiment_method": "not-run-amharic-not-validated"}
    if not re.search(r"[A-Za-z]", text):
        return {"sentiment": "unsupported", "sentiment_score": None, "sentiment_method": "not-run-language-unknown"}
    score = float(VADER.polarity_scores(text)["compound"])
    label = "positive" if score >= 0.05 else "negative" if score <= -0.05 else "neutral"
    return {"sentiment": label, "sentiment_score": round(score, 4), "sentiment_method": "vader-lexicon"}


def _get_spacy_model():
    global _SPACY_NLP, _SPACY_ATTEMPTED
    if _SPACY_ATTEMPTED:
        return _SPACY_NLP
    _SPACY_ATTEMPTED = True
    try:
        import spacy
        _SPACY_NLP = spacy.load("en_core_web_sm")
    except (ImportError, OSError):
        _SPACY_NLP = None
    return _SPACY_NLP


def extract_entities(text: str, language: str = "en") -> tuple[list[dict[str, str]], str]:
    if language.lower().startswith("am") or _ETHIOPIC.search(text):
        return [], "unavailable-unvalidated-for-amharic"
    nlp = _get_spacy_model()
    if nlp is not None:
        doc = nlp(text[:3000])
        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents
                    if ent.label_ in {"PERSON", "ORG", "GPE", "LOC", "EVENT", "PRODUCT"}]
        unique = list({(e["text"], e["label"]): e for e in entities}.values())
        return unique[:12], "spacy-en_core_web_sm"
    candidates = []
    for phrase in _ENTITY_FALLBACK.findall(text):
        phrase = phrase.strip()
        if phrase in _NON_ENTITIES or len(phrase) < 3:
            continue
        if phrase not in candidates:
            candidates.append(phrase)
    return [{"text": name, "label": "PROPER_NOUN_CANDIDATE"} for name in candidates[:12]], "capitalization-heuristic-fallback"


def make_brief(title: str, summary: str, max_chars: int = 360) -> str:
    """Create a short extractive brief from the publisher-provided RSS description."""
    source_text = re.sub(r"\s+", " ", summary or "").strip()
    if not source_text:
        return title.strip()
    sentences = re.split(r"(?<=[.!?])\s+", source_text)
    brief = " ".join(sentences[:2]).strip() or source_text
    if len(brief) > max_chars:
        brief = brief[:max_chars].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return brief


def cluster_stories(articles: list[dict[str, Any]], threshold: float = 0.34) -> list[dict[str, Any]]:
    """Group near-duplicate coverage using TF-IDF cosine similarity and connected components."""
    enriched = [dict(a) for a in articles]
    for item in enriched:
        item["cluster_id"] = ""
        item["cluster_size"] = 1
    if len(enriched) < 2:
        return enriched
    texts = [(item.get("title", "") + " " + item.get("summary", "")) for item in enriched]
    if not any(t.strip() for t in texts):
        return enriched
    try:
        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=5000, sublinear_tf=True).fit_transform(texts)
    except ValueError:
        return enriched
    similarities = (matrix @ matrix.T).toarray()
    parents = list(range(len(enriched)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for i in range(len(enriched)):
        for j in range(i + 1, len(enriched)):
            if similarities[i, j] >= threshold:
                ri, rj = root(i), root(j)
                parents[rj] = ri
    groups: dict[int, list[int]] = {}
    for index in range(len(enriched)):
        groups.setdefault(root(index), []).append(index)
    for indices in groups.values():
        if len(indices) < 2:
            continue
        key = ":".join(sorted(str(enriched[i].get("id", i)) for i in indices))
        cluster_id = "story-" + hashlib.sha1(key.encode()).hexdigest()[:8]
        for index in indices:
            enriched[index]["cluster_id"] = cluster_id
            enriched[index]["cluster_size"] = len(indices)
    return enriched


def analyze_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for raw in articles:
        item = dict(raw)
        text = f"{item.get('title', '')}. {item.get('summary', '')}".strip()
        if item.get("language", "en").lower().startswith("am") or _ETHIOPIC.search(text):
            topic, evidence, method = "unclassified", None, "not-run-amharic-not-validated"
        else:
            topic, evidence, method = classify_topic(text)
        item.update({"topic": topic, "topic_evidence_share": evidence, "topic_method": method})
        item.update(sentiment(text, item.get("language", "en")))
        entities, entity_method = extract_entities(text, item.get("language", "en"))
        item["entities"] = entities
        item["entity_method"] = entity_method
        item["brief_summary"] = make_brief(item.get("title", ""), item.get("summary", ""))
        results.append(item)
    return cluster_stories(results)
