"""条目校验：五类之内、必须有接收人。"""

from __future__ import annotations

from ..models import CATEGORIES, Finding, Item

PENALTY_CATEGORY = 3
PENALTY_OWNER = 4


def check(items: list[Item]) -> list[Finding]:
    out: list[Finding] = []
    for it in items:
        if it.category not in CATEGORIES:
            out.append(
                Finding("item.category", f"{it.title} 归到「{it.category}」，不在五类里", PENALTY_CATEGORY, str(it.id))
            )
        if not it.receiver.strip():
            out.append(
                Finding("item.no_owner", f"{it.title} 没写接收人", PENALTY_OWNER, str(it.id))
            )
    return out


def by_category(items: list[Item]) -> dict[str, int]:
    out = {c: 0 for c in CATEGORIES}
    for it in items:
        out[it.category] = out.get(it.category, 0) + 1
    return out


def open_items(items: list[Item]) -> list[Item]:
    return [it for it in items if not it.done]
