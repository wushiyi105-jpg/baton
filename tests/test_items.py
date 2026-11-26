from __future__ import annotations

from baton.domain.models import Item
from baton.domain.rules.items import by_category, check, open_items


def test_bad_category_flagged():
    findings = check([Item(1, 1, "杂项", "钥匙", "行政")])
    assert findings[0].rule_id == "item.category"


def test_empty_receiver_flagged():
    findings = check([Item(1, 1, "账号", "后台", "  ")])
    assert findings[0].rule_id == "item.no_owner"


def test_good_item_clean():
    assert check([Item(1, 1, "文档", "SOP", "阿岚")]) == []


def test_by_category_counts_all_five():
    counts = by_category([Item(1, 1, "账号", "a", "x")])
    assert set(counts) == {"账号", "文档", "客户", "代码", "流程"}
    assert counts["账号"] == 1


def test_open_items_excludes_done():
    items = [Item(1, 1, "账号", "a", "x", done=True), Item(2, 1, "文档", "b", "y")]
    assert [i.id for i in open_items(items)] == [2]
