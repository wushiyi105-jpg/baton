"""交接单：勾选回填、账号勾选即回收、签字后锁定。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from baton.adapters.store import SqliteStore
from baton.app.checklist import apply_checklist, build_checklist


def _store(tmp_path: Path) -> tuple[SqliteStore, int]:
    store = SqliteStore(tmp_path / "baton.db")
    iid = store.add_instance("小周", "运营专员", date(2026, 11, 28))
    store.add_item(iid, "账号", "后台账号", "阿岚", done=True, revoked=False)
    store.add_item(iid, "文档", "活动 SOP", "阿岚", done=False)
    return store, iid


def test_checklist_marks_permission(tmp_path) -> None:
    store, iid = _store(tmp_path)
    text = build_checklist(store, iid, date(2026, 11, 27))
    assert "- [ ] #1 后台账号 → 阿岚｜⚠ 权限未回收" in text
    assert "不能签字" in text
    assert "10 条高频遗漏" in text


def test_apply_ticks_account_and_revokes(tmp_path) -> None:
    store, iid = _store(tmp_path)
    text = build_checklist(store, iid, date(2026, 11, 27))
    file = tmp_path / "handover.md"
    file.write_text(text.replace("- [ ] #1", "- [x] #1"), encoding="utf-8")
    seen, changed = apply_checklist(store, iid, file)
    assert seen >= 2 and changed >= 1
    item = store.list_items(iid)[0]
    assert item.done and item.revoked


def test_apply_refused_after_sign(tmp_path) -> None:
    store, iid = _store(tmp_path)
    store.add_signoff(iid, date(2026, 11, 27), "已签")
    file = tmp_path / "handover.md"
    file.write_text("- [x] #1 后台账号", encoding="utf-8")
    with pytest.raises(ValueError, match="锁定"):
        apply_checklist(store, iid, file)


def test_apply_bad_file(tmp_path) -> None:
    store, iid = _store(tmp_path)
    file = tmp_path / "bad.md"
    file.write_text("没有勾选行", encoding="utf-8")
    with pytest.raises(ValueError, match="没有 `- \\[ \\] #id`"):
        apply_checklist(store, iid, file)
