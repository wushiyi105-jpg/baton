"""交接模板库：6 个岗位、10 条高频遗漏、权限清单。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA = Path(__file__).resolve().parents[2] / "data"


@lru_cache(maxsize=1)
def _data() -> dict[str, Any]:
    return json.loads((DATA / "roles.json").read_text(encoding="utf-8"))


def roles() -> list[dict[str, Any]]:
    return list(_data()["roles"])


def items_for(role: str) -> list[str]:
    for r in roles():
        if r["role"] == role:
            return list(r["items"])
    return []


def omissions() -> list[dict[str, str]]:
    return list(_data()["omissions"])


def permissions() -> list[dict[str, str]]:
    return list(_data()["permissions"])
