"""领域对象：交接实例、条目、签字。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

CATEGORIES = ("账号", "文档", "客户", "代码", "流程")


@dataclass(frozen=True)
class Instance:
    id: int
    who: str
    role: str
    due_on: date


@dataclass(frozen=True)
class Item:
    id: int
    instance_id: int
    category: str
    title: str
    receiver: str = ""
    done: bool = False
    revoked: bool = True


@dataclass(frozen=True)
class Signoff:
    id: int
    instance_id: int
    signed_on: date
    note: str = ""


@dataclass
class Finding:
    rule_id: str
    message: str
    penalty: int
    target: str = ""


@dataclass
class Check:
    instance: Instance | None = None
    total: int = 0
    done: int = 0
    findings: list[Finding] = field(default_factory=list)

    @property
    def progress(self) -> float:
        return self.done / self.total if self.total else 0.0

    @property
    def penalty_total(self) -> int:
        return sum(f.penalty for f in self.findings)

    @property
    def blockers(self) -> list[str]:
        return [f.message for f in self.findings if f.rule_id == "access.open"]

    @property
    def can_sign(self) -> bool:
        return not self.blockers
