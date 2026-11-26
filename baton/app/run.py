"""用例：按模板建条目 → 校验 → 签字闸门 → 模型写交接说明。"""

from __future__ import annotations

import json
from datetime import date

from ..adapters.llm import build_llm
from ..adapters.store import SqliteStore
from ..config import Settings
from ..domain.engine import build, groups, left, opener, sign
from ..domain.models import Check, Signoff

PROMPT = """按给出的条目写一段交接说明，分五类列，每条一句话。
只说输入里有的条目与接收人，不要补充没写的人名或日期。输出 JSON：{"text": "…"}"""


def check(store: SqliteStore, iid: int, today: date | None = None) -> Check:
    return build(store.instance(iid), store.list_items(iid), today or date.today())


def from_template(store: SqliteStore, iid: int) -> int:
    inst = store.instance(iid)
    if inst is None:
        raise ValueError("没有这个交接实例")
    n = 0
    for cat, title in store.templates(inst.role):
        store.add_item(iid, cat, title)
        n += 1
    return n


def sign_instance(store: SqliteStore, iid: int, today: date | None = None) -> Signoff:
    c = check(store, iid, today)
    s = sign(c, today or date.today())
    store.add_signoff(iid, s.signed_on)
    return s


def handover_note(store: SqliteStore, settings: Settings, iid: int) -> tuple[str, list[str]]:
    if not settings.llm_enabled:
        return "", []
    items = store.list_items(iid)
    facts = [f"{it.category}|{it.title}|{it.receiver}" for it in items]
    llm = build_llm(settings.llm_base_url, settings.llm_api_key, settings.llm_model, PROMPT)
    try:
        data = json.loads(llm.write(PROMPT, "\n".join(facts)))
    except Exception:  # noqa: BLE001
        return "", []
    text = str(data.get("text", ""))
    return text, []


def overview(store: SqliteStore, iid: int, today: date | None = None) -> dict[str, object]:
    t = today or date.today()
    c = check(store, iid, t)
    inst = store.instance(iid)
    return {
        "progress": c.progress,
        "groups": groups(store.list_items(iid)),
        "open": [i.title for i in opener(store.list_items(iid))],
        "left": left(inst, t) if inst else 0,
        "can_sign": c.can_sign,
    }
