from __future__ import annotations

import pytest

from baton.adapters.store import SqliteStore
from baton.config import Settings


@pytest.fixture()
def store(tmp_path) -> SqliteStore:
    return SqliteStore(tmp_path / "t.db")


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(db_path=tmp_path / "t.db", llm_api_key="", port=8009)


@pytest.fixture()
def iid(store) -> int:
    import datetime

    return store.add_instance("小周", "运营专员", datetime.date(2026, 11, 28))
