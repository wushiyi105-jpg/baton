"""逾期：交接日过了还有没做完的条目。"""

from __future__ import annotations

from datetime import date

from ..models import Finding, Instance, Item

PENALTY = 6


def days_left(instance: Instance, today: date) -> int:
    return (instance.due_on - today).days


def check(instance: Instance, items: list[Item], today: date) -> list[Finding]:
    left = days_left(instance, today)
    opened = [it for it in items if not it.done]
    if left >= 0 or not opened:
        return []
    return [
        Finding(
            "handover.overdue",
            f"交接日已过 {-left} 天，还有 {len(opened)} 条没做完：{'、'.join(it.title for it in opened[:3])}",
            PENALTY,
            instance.who,
        )
    ]
