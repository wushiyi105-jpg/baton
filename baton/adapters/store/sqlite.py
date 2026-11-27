"""SQLite：templates / instances / items / signoffs。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Boolean, Date, Integer, String, inspect, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker
from sqlalchemy.orm import Session as OrmSession

from ...domain.models import CATEGORIES, Instance, Item, Signoff
from .base import Base, make_engine, make_session


class InstanceRow(Base):
    __tablename__ = "instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    who: Mapped[str] = mapped_column(String(40))
    role: Mapped[str] = mapped_column(String(60), default="")
    due_on: Mapped[date] = mapped_column(Date)


class ItemRow(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(120))
    receiver: Mapped[str] = mapped_column(String(40), default="")
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=True)


class SignoffRow(Base):
    __tablename__ = "signoffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instance_id: Mapped[int] = mapped_column(Integer)
    signed_on: Mapped[date] = mapped_column(Date)
    note: Mapped[str] = mapped_column(String(200), default="")


class TemplateRow(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role: Mapped[str] = mapped_column(String(60))
    category: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(120))


def _upgrade_schema(engine) -> None:
    root = next(p for p in Path(__file__).resolve().parents if (p / "alembic.ini").exists())
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{engine.url.database}")
    command.upgrade(cfg, "head")


class SqliteStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.engine = make_engine(self.path)
        self.session: sessionmaker[OrmSession] = make_session(self.engine)
        self.init_schema()

    def init_schema(self) -> None:
        _upgrade_schema(self.engine)

    def schema_ok(self) -> bool:
        return {"templates", "instances", "items", "signoffs"} <= set(inspect(self.engine).get_table_names())

    def summary(self) -> str:
        return f"{len(self.list_instances())} 个交接、{len(self.list_items())} 条条目"

    def add_template(self, role: str, category: str, title: str) -> int:
        if category not in CATEGORIES:
            raise ValueError(f"没有这一类：{category}")
        with self.session() as s:
            row = TemplateRow(role=role, category=category, title=title)
            s.add(row)
            s.commit()
            return int(row.id)

    def templates(self, role: str) -> list[tuple[str, str]]:
        with self.session() as s:
            rows = s.scalars(select(TemplateRow).where(TemplateRow.role == role)).all()
        return [(r.category, r.title) for r in rows]

    def add_instance(self, who: str, role: str, due_on: date) -> int:
        with self.session() as s:
            row = InstanceRow(who=who, role=role, due_on=due_on)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_instances(self) -> list[Instance]:
        with self.session() as s:
            rows = s.scalars(select(InstanceRow)).all()
        return [Instance(r.id, r.who, r.role, r.due_on) for r in rows]

    def instance(self, iid: int) -> Instance | None:
        with self.session() as s:
            row = s.scalars(select(InstanceRow).where(InstanceRow.id == iid)).first()
        return Instance(row.id, row.who, row.role, row.due_on) if row else None

    def add_item(self, instance_id: int, category: str, title: str, receiver: str = "", done: bool = False, revoked: bool = True) -> int:
        if not category.strip():
            raise ValueError("分类不能为空")
        with self.session() as s:
            row = ItemRow(instance_id=instance_id, category=category, title=title, receiver=receiver, done=done, revoked=revoked)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_items(self, instance_id: int | None = None) -> list[Item]:
        with self.session() as s:
            q = select(ItemRow)
            if instance_id is not None:
                q = q.where(ItemRow.instance_id == instance_id)
            rows = s.scalars(q).all()
        return [Item(r.id, r.instance_id, r.category, r.title, r.receiver, r.done, r.revoked) for r in rows]

    def tick(self, item_id: int, revoked: bool | None = None) -> bool:
        with self.session() as s:
            row = s.scalars(select(ItemRow).where(ItemRow.id == item_id)).first()
            if row is None:
                return False
            row.done = True
            if revoked is not None:
                row.revoked = revoked
            s.commit()
            return True

    def add_signoff(self, instance_id: int, signed_on: date, note: str = "") -> int:
        with self.session() as s:
            row = SignoffRow(instance_id=instance_id, signed_on=signed_on, note=note)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_signoffs(self) -> list[Signoff]:
        with self.session() as s:
            rows = s.scalars(select(SignoffRow)).all()
        return [Signoff(r.id, r.instance_id, r.signed_on, r.note) for r in rows]
