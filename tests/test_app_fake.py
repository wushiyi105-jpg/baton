"""真实内存 Store 跑 check：不建 SQLite，mypy 校验 StorePort。"""

from __future__ import annotations

from datetime import date

from baton.app.run import check
from baton.domain.models import Instance, Item
from baton.ports import StorePort


class InMemoryStore:
    def instance(self, iid: int) -> Instance | None:
        return None

    def list_items(self, iid: int) -> list[Item]:
        return []

    def templates(self, role: str) -> list[tuple[str, str]]:
        return []

    def add_item(self, iid: int, category: str, title: str) -> int:
        return 1

    def add_signoff(self, instance_id: int, signed_on: date, note: str = "") -> int:
        return 1


def test_check_with_memory_store() -> None:
    store: StorePort = InMemoryStore()
    out = check(store, 1, date(2026, 1, 5))
    assert out.total == 0
