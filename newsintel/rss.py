from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import requests

from .models import Article, FeedSource

USER_AGENT = "AI-News-Intelligence/0.1 (+RSS metadata reader; portfolio project)"
MAX_FEED_BYTES = 5_000_000


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data.strip())


def clean_feed_text(value: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(value or "")
        parser.close()
        text = " ".join(parser.parts)
    except Exception:  # noqa: BLE001 - malformed publisher HTML should fall back to plain text instead of dropping the feed item.
        text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return ""
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not (k.lower().startswith("utm_") or k.lower() in {"fbclid", "gclid", "mc_cid", "mc_eid", "ref"})]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", urlencode(query), ""))


def _published(entry: dict) -> str:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return ""
    try:
        return datetime(*parsed[:6], tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError):
        return ""


def _entry_summary(entry: dict) -> str:
    raw = entry.get("summary", "")
    if not raw and entry.get("content"):
        raw = entry["content"][0].get("value", "")
    return clean_feed_text(str(raw))[:1200]


def parse_feed_content(source: FeedSource, content: bytes, limit: int = 100) -> list[Article]:
    """Parse an RSS/Atom payload into normalized, attribution-preserving records."""
    parsed = feedparser.parse(content)
    articles: list[Article] = []
    for entry in parsed.entries[:limit]:
        title = clean_feed_text(str(entry.get("title", "")))
        url = canonicalize_url(str(entry.get("link", "")))
        if not title or not url:
            continue
        uid = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
        tags = entry.get("tags") or []
        category = clean_feed_text(str(tags[0].get("term", ""))) if tags else ""
        articles.append(Article(
            id=uid,
            title=title,
            url=url,
            source=source.name,
            source_homepage=source.homepage,
            attribution=source.attribution or source.name,
            published=_published(entry),
            summary=_entry_summary(entry),
            language=source.language,
            region=source.region,
            feed_category=category,
        ))
    return articles


def load_sources(path: str | Path) -> list[FeedSource]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise TypeError("Feed configuration must be a JSON list")
    sources = [FeedSource.from_dict(row) for row in raw]
    if not sources:
        raise ValueError("At least one feed source is required")
    return sources


def fetch_one(source: FeedSource, timeout: float = 12.0, limit: int = 100,
              session: requests.Session | None = None) -> list[Article]:
    client = session or requests.Session()
    response = client.get(source.url, timeout=timeout, headers={"User-Agent": USER_AGENT}, stream=True)
    response.raise_for_status()
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=65536):
        total += len(chunk)
        if total > MAX_FEED_BYTES:
            raise ValueError(f"Feed exceeds {MAX_FEED_BYTES} byte safety limit")
        chunks.append(chunk)
    return parse_feed_content(source, b"".join(chunks), limit=limit)


def collect(sources: list[FeedSource], timeout: float = 12.0, per_feed_limit: int = 100,
            session: requests.Session | None = None) -> tuple[list[Article], list[str]]:
    """Fetch feeds sequentially (polite, predictable load); return partial results plus errors."""
    collected: list[Article] = []
    errors: list[str] = []
    client = session or requests.Session()
    for source in sources:
        try:
            collected.extend(fetch_one(source, timeout=timeout, limit=per_feed_limit, session=client))
        except (requests.RequestException, ValueError, OSError) as exc:
            errors.append(f"{source.name}: {type(exc).__name__}: {exc}")
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[Article] = []
    for article in collected:
        title_key = re.sub(r"[^\w]+", " ", article.title.casefold()).strip()
        if article.id in seen_ids or (title_key and title_key in seen_titles):
            continue
        seen_ids.add(article.id)
        seen_titles.add(title_key)
        unique.append(article)
    unique.sort(key=lambda a: a.published, reverse=True)
    return unique, errors
