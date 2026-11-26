"""本地核算：进度、阻塞、逾期，签字闸门。"""

from __future__ import annotations

from datetime import date

from .models import Check, Finding, Instance, Item, Signoff
from .rules.access import check as access_check
from .rules.deadline import check as deadline_check
from .rules.deadline import days_left
from .rules.items import by_category, open_items
from .rules.items import check as item_check


def build(instance: Instance | None, items: list[Item], today: date) -> Check:
    c = Check(instance=instance, total=len(items), done=len([i for i in items if i.done]))
    if instance is None:
        return c
    findings: list[Finding] = []
    findings += item_check(items)
    findings += access_check(items)
    findings += deadline_check(instance, items, today)
    c.findings = findings
    return c


def groups(items: list[Item]) -> dict[str, int]:
    return by_category(items)


def opener(items: list[Item]) -> list[Item]:
    return open_items(items)


def left(instance: Instance, today: date) -> int:
    return days_left(instance, today)


def sign(c: Check, today: date, note: str = "") -> Signoff:
    if not c.can_sign:
        raise ValueError("还有权限没回收：" + "；".join(c.blockers))
    if c.instance is None:
        raise ValueError("没有交接实例")
    return Signoff(0, c.instance.id, today, note)
