"""交接单：可勾选 Markdown，勾完能回填数据库；签字后锁定。"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from ..domain.catalog import omissions
from ..domain.models import CATEGORIES, Item
from ..ports import StorePort
from .run import check


def _signed(store: StorePort, iid: int) -> str:
    for s in store.list_signoffs():
        if s.instance_id == iid:
            return s.signed_on.isoformat()
    return ""


def build_checklist(store: StorePort, iid: int, today: date) -> str:
    c = check(store, iid, today)
    if c.instance is None:
        raise ValueError(f"没有交接实例 #{iid}")
    signed_on = _signed(store, iid)
    items = store.list_items(iid)
    by_cat: dict[str, list[Item]] = {k: [] for k in CATEGORIES}
    for it in items:
        by_cat.setdefault(it.category, []).append(it)

    lines = [
        f"# 交接清单 · {c.instance.who}（{c.instance.role}）",
        "",
        f"> 截止 {c.instance.due_on.isoformat()}；进度 {c.done}/{c.total}（{c.progress:.0%}）。"
        + (f"**已于 {signed_on} 签字，清单锁定。**" if signed_on else "**未签字。**"),
        "",
        "> 勾选说明：把 `- [ ]` 改成 `- [x]` 表示已完成；账号类的勾选同时代表权限已回收。"
        "改完执行 `baton apply --file 本文件` 回填。",
        "",
        "## 一、逐项清单",
        "",
    ]
    for cat in CATEGORIES:
        group = by_cat.get(cat, [])
        if not group:
            continue
        lines += [f"### {cat}", ""]
        for it in group:
            checked = it.done and (it.revoked if cat == "账号" else True)
            box = "x" if checked else " "
            extra = ""
            if cat == "账号":
                extra = "｜权限已回收" if it.revoked else "｜⚠ 权限未回收"
            lines.append(f"- [{box}] #{it.id} {it.title} → {it.receiver or '（未填接收人）'}{extra}")
        lines.append("")

    lines += ["## 二、权限回收（未回收不能签字）", ""]
    accounts = [it for it in items if it.category == "账号"]
    if accounts:
        for it in accounts:
            lines.append(f"- {'✅' if it.revoked else '🔴'} {it.title}")
    else:
        lines.append("- 清单里没有账号类条目")
    lines.append("")

    lines += ["## 三、10 条高频遗漏（逐条对）", ""]
    for o in omissions():
        hits = [it for it in items if o["match"] in it.title]
        if hits:
            ok = all(it.done for it in hits)
            lines.append(f"- [{'x' if ok else ' '}] {o['text']}（对应 #{hits[0].id}）")
        else:
            lines.append(f"- [ ] {o['text']}（清单里没有，补一条）")
    lines.append("")

    lines += ["## 四、签字", ""]
    if signed_on:
        lines.append(f"- 已签字：{signed_on}。清单锁定，不能再 apply。")
    elif c.can_sign:
        lines.append("- 权限已全部回收，可以签字：`baton sign --iid " + str(iid) + "`")
    else:
        lines.append("- **不能签字**，还卡在这些权限：")
        lines += [f"  - {b}" for b in c.blockers]
    lines += [
        "",
        "签字人：________________    日期：________________",
        "",
        "---",
        "",
        f"清单共 {c.total} 条，已完成 {c.done} 条；扣分 {c.penalty_total}。",
        "",
    ]
    return "\n".join(lines)


_PATTERN = re.compile(r"- \[([ xX])\] #(\d+)")


def apply_checklist(store: StorePort, iid: int, path: Path) -> tuple[int, int]:
    if _signed(store, iid):
        raise ValueError("这个交接已经签字，清单锁定，不能再改")
    items = {it.id: it for it in store.list_items(iid)}
    changed = 0
    seen = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        m = _PATTERN.search(line)
        if not m:
            continue
        seen += 1
        item = items.get(int(m.group(2)))
        if item is None:
            continue
        done = m.group(1).lower() == "x"
        revoked = done if item.category == "账号" else None
        if item.done == done and (revoked is None or item.revoked == revoked):
            continue
        if store.set_item_state(item.id, done, revoked):
            changed += 1
    if seen == 0:
        raise ValueError("文件里没有 `- [ ] #id` 格式的行，未做任何修改")
    return seen, changed
