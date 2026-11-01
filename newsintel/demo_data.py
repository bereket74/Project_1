"""Fictional records for UI demonstrations; never mix these with live news data."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def synthetic_articles(now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    examples = [
        ("Synthetic example: Farmers test drought-resistant wheat", "A fictional pilot explores water-saving methods for this dashboard demo.", 1),
        ("Synthetic example: Community restores soil after a dry season", "This invented story demonstrates climate topic tags and trend counts.", 3),
        ("Synthetic example: Researchers test water-saving irrigation", "An entirely fictional study is included only to demonstrate topic analysis.", 8),
        ("Synthetic example: Transit office pilots electric buses", "A made-up city pilot illustrates technology and search controls.", 2),
        ("Synthetic example: Local clinic expands vaccination outreach", "This fictional health update is not a real public-health announcement.", 4),
        ("Synthetic example: Coffee cooperative explores a new trade model", "A fictional business scenario demonstrates filters and topic summaries.", 9),
        ("Synthetic example: የፀሐይ ኃይል ፕሮጀክት ተጀመረ", "ይህ ለማሳያ ብቻ የተፈጠረ ምናባዊ የዜና ናሙና ነው።", 1),
    ]
    rows = []
    for index, (title, summary, age_days) in enumerate(examples, start=1):
        rows.append({
            "id": f"synthetic-{index:02d}",
            "title": title,
            "url": "",
            "source": "Synthetic sample",
            "source_homepage": "",
            "attribution": "Synthetic demo data — not a real publisher",
            "published": (now - timedelta(days=age_days)).isoformat().replace("+00:00", "Z"),
            "summary": summary,
            "language": "am" if "\u1200" <= title[title.find(":") + 2:title.find(":") + 3] <= "\u137f" else "en",
            "region": "ethiopia",
            "feed_category": "synthetic",
        })
    return rows
