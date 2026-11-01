from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def save_cache(path: str | Path, articles: list[dict[str, Any]]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "articles": articles}
    fd, temp_name = tempfile.mkstemp(prefix=target.name + ".", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_cache(path: str | Path) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    payload = json.loads(target.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("articles"), list):
        raise ValueError("Unsupported or malformed cache file")
    return payload["articles"]
