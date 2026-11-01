from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from .pipeline import run_intelligence
from .rss import load_sources
from .storage import load_cache, save_cache

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze news RSS metadata without scraping full articles.")
    parser.add_argument("--sources", default=str(PROJECT_ROOT / "config" / "feeds.json"))
    parser.add_argument("--output", default="", help="Optional .json or .csv output path")
    parser.add_argument("--cache", default=str(PROJECT_ROOT / "data" / "latest_articles.json"))
    parser.add_argument("--cached", action="store_true", help="Print the last local cache; do not access the network")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--per-feed-limit", type=int, default=100)
    args = parser.parse_args()

    if args.cached:
        articles = load_cache(args.cache)
        errors: list[str] = []
    else:
        sources = load_sources(args.sources)
        articles, errors = run_intelligence(sources, timeout=args.timeout, per_feed_limit=args.per_feed_limit)
        if articles:
            save_cache(args.cache, articles)
    for message in errors:
        print(f"WARNING: {message}", file=sys.stderr)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.suffix.lower() == ".csv":
            columns = ["id", "title", "url", "source", "published", "topic", "sentiment", "sentiment_score", "cluster_id", "brief_summary", "region", "language"]
            with output.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(articles)
        else:
            output.write_text(json.dumps(articles, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {len(articles)} analyzed items to {output}")
    else:
        print(json.dumps(articles, ensure_ascii=False, indent=2))
    print(f"Analyzed articles: {len(articles)}; feed warnings: {len(errors)}", file=sys.stderr)
    return 0 if articles or not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
