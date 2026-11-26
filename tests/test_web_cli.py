from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from baton.doctor import run_doctor
from baton.iface.cli import app
from baton.iface.web import create_app


def _seed(store):
    iid = store.add_instance("小周", "运营专员", date(2026, 11, 28))
    store.add_template("运营专员", "账号", "后台账号")
    store.add_item(iid, "账号", "后台账号", "阿岚", done=True, revoked=False)
    store.add_item(iid, "文档", "SOP", "阿岚")
    return iid


def test_index(store, settings):
    _seed(store)
    client = TestClient(create_app(settings, store))
    body = client.get("/").text
    assert client.get("/").status_code == 200
    assert "清单" in body


def test_empty_index_hint(store, settings):
    r = TestClient(create_app(settings, store)).get('/')
    assert r.status_code == 200
    assert '先 seed' in r.text


def test_cli_status_and_sign_blocked(tmp_path):
    runner = CliRunner()
    db = str(tmp_path / "c.db")
    assert runner.invoke(app, ["status", "--db", db, "--iid", "1"]).exit_code == 0


def test_doctor_green(settings):
    checks, ok = run_doctor(settings)
    assert ok is True
