from __future__ import annotations

from datetime import date

from baton.domain.engine import build, groups, left, sign
from baton.domain.models import Instance, Item


def _inst() -> Instance:
    return Instance(1, "小周", "运营专员", date(2026, 11, 28))


def test_progress_and_penalty():
    items = [Item(1, 1, "账号", "后台", "阿岚", done=True), Item(2, 1, "代码", "脚本", "小何")]
    c = build(_inst(), items, date(2026, 11, 27))
    assert c.progress == 0.5
    assert c.total == 2


def test_groups_counts():
    asserts = groups([Item(1, 1, "账号", "a", "x"), Item(2, 1, "账号", "b", "y")])
    assert asserts["账号"] == 2


def test_left_negative_after_due():
    assert left(_inst(), date(2026, 12, 1)) == -3


def test_sign_blocked_by_open_access():
    items = [Item(1, 1, "账号", "后台", "阿岚", done=True, revoked=False)]
    c = build(_inst(), items, date(2026, 11, 27))
    assert c.can_sign is False
    try:
        sign(c, date(2026, 11, 27))
    except ValueError as e:
        assert "权限" in str(e)
    else:
        raise AssertionError("应该拒绝签字")


def test_sign_ok_when_clean():
    items = [Item(1, 1, "账号", "后台", "阿岚", done=True, revoked=True)]
    c = build(_inst(), items, date(2026, 11, 27))
    s = sign(c, date(2026, 11, 27))
    assert s.instance_id == 1


def test_sign_without_instance_raises():
    try:
        sign(build(None, [], date(2026, 11, 27)), date(2026, 11, 27))
    except ValueError:
        pass
    else:
        raise AssertionError("应该报错")
