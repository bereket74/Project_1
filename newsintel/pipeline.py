from __future__ import annotations

from typing import Any

from .analysis import analyze_articles
from .models import FeedSource
from .rss import collect


def run_intelligence(sources: list[FeedSource], timeout: float = 12.0,
                     per_feed_limit: int = 100) -> tuple[list[dict[str, Any]], list[str]]:
    articles, errors = collect(sources, timeout=timeout, per_feed_limit=per_feed_limit)
    return analyze_articles([article.to_dict() for article in articles]), errors
