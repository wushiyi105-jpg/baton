"""用例：按模板建条目 → 校验 → 签字闸门 → 模型写交接说明。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ..config import Settings
from ..domain.engine import build, groups, left, opener, sign
from ..domain.models import Check, Signoff
from ..ports import LLMPort, StorePort

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "handover.md").read_text(encoding="utf-8")


def parse_json(text: str) -> dict:
    """模型常把 JSON 包在 ```json 里；取出第一个完整对象再解析。"""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json object")
    return json.loads(text[start : end + 1])


def check(store: StorePort, iid: int, today: date | None = None) -> Check:
    return build(store.instance(iid), store.list_items(iid), today or date.today())


def from_template(store: StorePort, iid: int) -> int:
    inst = store.instance(iid)
    if inst is None:
        raise ValueError("没有这个交接实例")
    n = 0
    for cat, title in store.templates(inst.role):
        store.add_item(iid, cat, title)
        n += 1
    return n


def sign_instance(store: StorePort, iid: int, today: date | None = None) -> Signoff:
    c = check(store, iid, today)
    s = sign(c, today or date.today())
    store.add_signoff(iid, s.signed_on)
    return s


def handover_note(
    store: StorePort, settings: Settings, iid: int, llm: LLMPort | None = None
) -> tuple[str, list[str]]:
    if llm is None:
        return "", []
    items = store.list_items(iid)
    facts = [f"{it.category}|{it.title}|{it.receiver}" for it in items]
    try:
        data = parse_json(llm.write(PROMPT, "\n".join(facts)))
    except Exception:  # noqa: BLE001
        return "", []
    text = str(data.get("text", ""))
    return text, []


def overview(store: StorePort, iid: int, today: date | None = None) -> dict[str, object]:
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
