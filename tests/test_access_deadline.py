from __future__ import annotations

from datetime import date

from baton.domain.models import Instance, Item
from baton.domain.rules.access import account_titles, revoked_all
from baton.domain.rules.access import check as a_check
from baton.domain.rules.deadline import check as d_check
from baton.domain.rules.deadline import days_left


def test_not_revoked_blocks():
    findings = a_check([Item(1, 1, "账号", "后台", "阿岚", done=True, revoked=False)])
    assert findings[0].rule_id == "access.open"
    assert findings[0].penalty == 10


def test_revoked_ok():
    assert a_check([Item(1, 1, "账号", "后台", "阿岚", revoked=True)]) == []


def test_non_account_ignored():
    assert a_check([Item(1, 1, "文档", "SOP", "阿岚", revoked=False)]) == []


def test_revoked_all_semantics():
    items = [Item(1, 1, "账号", "a", "x", revoked=True), Item(2, 1, "文档", "b", "y", revoked=False)]
    assert revoked_all(items) is True


def test_account_titles():
    assert account_titles([Item(1, 1, "账号", "后台", "x"), Item(2, 1, "文档", "SOP", "y")]) == ["后台"]


def test_days_left():
    assert days_left(Instance(1, "小周", "运营", date(2026, 11, 28)), date(2026, 11, 27)) == 1


def test_not_overdue_before_due():
    inst = Instance(1, "小周", "运营", date(2026, 11, 28))
    assert d_check(inst, [Item(1, 1, "账号", "a", "x")], date(2026, 11, 27)) == []


def test_overdue_with_open_items():
    inst = Instance(1, "小周", "运营", date(2026, 11, 20))
    findings = d_check(inst, [Item(1, 1, "账号", "a", "x", done=True), Item(2, 1, "客户", "b", "y")], date(2026, 11, 27))
    assert findings[0].rule_id == "handover.overdue"


def test_overdue_but_all_done_no_finding():
    inst = Instance(1, "小周", "运营", date(2026, 11, 20))
    assert d_check(inst, [Item(1, 1, "账号", "a", "x", done=True)], date(2026, 11, 27)) == []
