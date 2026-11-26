"""权限回收：账号类条目没标回收，一律阻塞签字。"""

from __future__ import annotations

from ..models import Finding, Item

PENALTY = 10


def check(items: list[Item]) -> list[Finding]:
    out: list[Finding] = []
    for it in items:
        if it.category == "账号" and not it.revoked:
            out.append(
                Finding(
                    "access.open",
                    f"{it.title} 的权限还没回收，签字卡在这一条",
                    PENALTY,
                    str(it.id),
                )
            )
    return out


def revoked_all(items: list[Item]) -> bool:
    return all(it.revoked for it in items if it.category == "账号")


def account_titles(items: list[Item]) -> list[str]:
    return [it.title for it in items if it.category == "账号"]
