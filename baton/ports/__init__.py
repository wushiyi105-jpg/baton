"""端口：app 实际调用的方法集合，实现见 adapters。"""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from ..domain.models import Instance, Item


@runtime_checkable
class StorePort(Protocol):
    def instance(self, iid: int) -> Instance | None: ...

    def list_items(self, iid: int) -> list[Item]: ...

    def templates(self, role: str) -> list[tuple[str, str]]: ...

    def add_item(self, iid: int, category: str, title: str) -> int: ...

    def add_signoff(self, instance_id: int, signed_on: date, note: str = "") -> int: ...


@runtime_checkable
class LLMPort(Protocol):
    def write(self, system: str, facts: str) -> str: ...
