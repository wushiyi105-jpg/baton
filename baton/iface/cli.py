"""命令行：seed / status / tick / note / sign / doctor / serve。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from ..adapters.llm import build_llm
from ..adapters.notify import WebhookNotifier
from ..adapters.store import SqliteStore
from ..app.checklist import apply_checklist, build_checklist
from ..app.run import PROMPT, check, from_template, groups, handover_note, sign_instance
from ..config import Settings
from ..config import settings as default_settings
from ..doctor import main as doctor_main

app = typer.Typer(help="离职交接：权限没回收不签字", no_args_is_help=True)
console = Console()


def _settings(db: Path | None, port: int | None = None) -> Settings:
    s = default_settings.model_copy(deep=True)
    if db:
        s.db_path = db
    if port:
        s.port = port
    return s


def _store(settings: Settings) -> SqliteStore:
    return SqliteStore(settings.db_path)


def _notify(settings: Settings, text: str) -> None:
    if not text or not settings.webhook_url:
        return
    ok = WebhookNotifier(settings.webhook_url).send(text)
    console.print(f"[dim]webhook {'ok' if ok else 'failed'}[/]")


@app.command()
def seed(db: Path = typer.Option(None)) -> None:
    """写入模板、交接实例、条目。"""
    s = _settings(db)
    store = _store(s)
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seed.json").read_text(encoding="utf-8")
    )
    for t in data["templates"]:
        store.add_template(t["role"], t["category"], t["title"])
    ids = {}
    for inst in data["instances"]:
        ids[inst["who"]] = store.add_instance(inst["who"], inst["role"], date.fromisoformat(inst["due_on"]))
    for it in data["items"]:
        store.add_item(ids[it["who"]], it["category"], it["title"], it.get("receiver", ""), it.get("done", False), it.get("revoked", True))
    console.print(f"已写入 {len(data['templates'])} 条模板、{len(data['instances'])} 个交接、{len(data['items'])} 条条目")


@app.command()
def status(iid: int = typer.Option(1), day: str = typer.Option(""), db: Path = typer.Option(None)) -> None:
    """进度、分类、阻塞。"""
    store = _store(_settings(db))
    c = check(store, iid, date.fromisoformat(day) if day else None)
    console.print(f"{c.instance.who if c.instance else '?'}：{c.done}/{c.total}（{c.progress:.0%}）")
    console.print(f"分类：{groups(store.list_items(iid))}")
    for f in c.findings:
        console.print(f"  [yellow]{f.rule_id}[/] -{f.penalty} {f.message}")
    console.print(f"合计扣 {c.penalty_total} 分，{'可以签字' if c.can_sign else '不能签字'}")


@app.command()
def handover(
    iid: int = typer.Option(1, help="交接实例 id"),
    out: Path = typer.Option(None, help="输出可勾选 Markdown；不填打印"),
    day: str = typer.Option(""),
    db: Path = typer.Option(None),
) -> None:
    """可勾选交接单：权限没回收会挡在签字前。"""
    store = _store(_settings(db))
    try:
        body = build_checklist(store, iid, date.fromisoformat(day) if day else date.today())
    except ValueError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(code=2)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        console.print(f"[green]已写出[/] {out}（{len(body.splitlines())} 行）")
    else:
        console.print(body)


@app.command("apply")
def apply_cmd(
    file: Path = typer.Option(..., help="改过勾选的交接单"),
    iid: int = typer.Option(1, help="交接实例 id"),
    db: Path = typer.Option(None),
) -> None:
    """把交接单上的勾选回填数据库；已签字的单子拒绝修改。"""
    store = _store(_settings(db))
    if not file.exists():
        console.print(f"[red]找不到 {file}[/]")
        raise typer.Exit(code=2)
    try:
        seen, changed = apply_checklist(store, iid, file)
    except ValueError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(code=2)
    console.print(f"读到 {seen} 条勾选，更新 {changed} 条")


@app.command()
def tick(item: int = typer.Option(..., help="条目 id"), db: Path = typer.Option(None)) -> None:
    """把一条标成做完。"""
    store = _store(_settings(db))
    console.print("已勾" if store.tick(item) else "没有这条")


@app.command()
def fill(iid: int = typer.Option(1), db: Path = typer.Option(None)) -> None:
    """按模板补齐条目。"""
    store = _store(_settings(db))
    try:
        console.print(f"新增 {from_template(store, iid)} 条")
    except ValueError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(code=1)


@app.command()
def note(iid: int = typer.Option(1), db: Path = typer.Option(None)) -> None:
    """模型写交接说明（无 key 时不编）。"""
    s = _settings(db)
    llm = build_llm(s.llm_base_url, s.llm_api_key, s.llm_model, PROMPT) if s.llm_enabled else None
    text, _ = handover_note(_store(s), s, iid, llm)
    body = text or "模型没开，用 status 看清单"
    console.print(body)
    _notify(s, body)


@app.command()
def sign(iid: int = typer.Option(1), day: str = typer.Option(""), db: Path = typer.Option(None)) -> None:
    """签字；权限没回收会被拒。"""
    store = _store(_settings(db))
    try:
        s = sign_instance(store, iid, date.fromisoformat(day) if day else None)
    except ValueError as e:
        console.print(f"[red]不能签：{e}[/]")
        raise typer.Exit(code=2)
    console.print(f"已签：{s.signed_on}")


@app.command()
def doctor(db: Path = typer.Option(None)) -> None:
    """四项体检。"""
    raise typer.Exit(code=doctor_main(_settings(db)))


@app.command()
def serve(port: int = typer.Option(None), db: Path = typer.Option(None)) -> None:
    """Web 界面。"""
    import uvicorn

    from .web import create_app

    s = _settings(db, port)
    uvicorn.run(create_app(s), host="127.0.0.1", port=s.port)


if __name__ == "__main__":
    app()
