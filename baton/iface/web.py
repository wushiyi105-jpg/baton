"""FastAPI + Jinja2：交接清单。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..adapters.store import SqliteStore
from ..app.run import check
from ..config import Settings
from ..domain.engine import groups, left
from ..domain.rules.items import open_items

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


def create_app(settings: Settings, store: SqliteStore | None = None) -> FastAPI:
    app = FastAPI(title="Baton", version="1.0.0")
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parents[2] / "static")),
        name="static",
    )
    store = store or SqliteStore(settings.db_path)

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, iid: int = 1) -> HTMLResponse:
        inst = store.instance(iid)
        if inst is None:
            rows = store.list_instances()
            inst = rows[0] if rows else None
        if inst is None:
            return HTMLResponse("<p style='font-family:sans-serif'>还没有交接实例，先 seed。</p>")
        today = date.today()
        c = check(store, inst.id, today)
        return TEMPLATES.TemplateResponse(
            request, "index.html",
            {"c": c, "inst": inst, "items": store.list_items(inst.id), "open": open_items(store.list_items(inst.id)),
             "groups": groups(store.list_items(inst.id)), "left": left(inst, today), "today": today.isoformat(),
             "signoffs": [s for s in store.list_signoffs() if s.instance_id == inst.id]},
        )

    @app.post("/tick/{item_id}")
    def tick(item_id: int) -> dict[str, object]:
        return {"ok": store.tick(item_id)}

    @app.get("/status.txt", response_class=HTMLResponse)
    def status_txt(iid: int = 1) -> HTMLResponse:
        c = check(store, iid)
        text = f"{c.done}/{c.total} 完成，扣 {c.penalty_total}，{'可签' if c.can_sign else '被权限阻塞'}"
        return HTMLResponse(f"<pre>{text}</pre>")

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "items": len(store.list_items())}

    return app


def app_factory(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        from ..config import settings as default_settings

        settings = default_settings
    return create_app(settings)

