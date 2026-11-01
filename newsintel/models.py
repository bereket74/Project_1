from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class Article:
    """Only RSS-provided metadata and short feed descriptions; never full-page text."""

    id: str
    title: str
    url: str
    source: str
    source_homepage: str
    attribution: str
    published: str = ""
    summary: str = ""
    language: str = "unknown"
    region: str = "global"
    feed_category: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class FeedSource:
    name: str
    url: str
    homepage: str
    language: str = "en"
    region: str = "global"
    attribution: str = ""

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> FeedSource:
        return cls(
            name=str(raw["name"]),
            url=str(raw["url"]),
            homepage=str(raw.get("homepage", raw["url"])),
            language=str(raw.get("language", "unknown")),
            region=str(raw.get("region", "global")),
            attribution=str(raw.get("attribution", raw["name"])),
        )
