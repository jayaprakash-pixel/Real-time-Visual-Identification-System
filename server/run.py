"""Launcher: python server/run.py  (one process: AI pipeline thread + alerts + API + frontend)."""

import logging
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ai_vision"))   # the AI module lives beside the server

import uvicorn

from app import Services, create_app
from auth import Users
from bridge import Engine, MatchHandler, PersonSync
from config import Settings
from dispatch import Dispatcher
from gate import MatchGate
from hub import Hub
from store import Store
from telegram import Telegram

log = logging.getLogger("rtvis")


def secret_key(data_dir):
    """Token signing key: created once, kept in data/ (git-ignored), never in the repo."""
    path = data_dir / "secret.key"
    if not path.exists():
        path.write_bytes(secrets.token_bytes(32))
    return path.read_bytes()


def build(settings):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    store = Store(str(settings.data_dir / "server.db"))
    users = Users(store.db, store.lock, secret_key(settings.data_dir),
                  token_hours=settings.token_hours, allow_signup=settings.allow_signup)
    hub, dispatcher = Hub(), Dispatcher()
    dispatcher.add("websocket", hub.broadcast)
    telegram = Telegram(settings.telegram_token, settings.telegram_chat_id)
    if telegram.enabled:
        dispatcher.add("telegram", telegram)
    handler = MatchHandler(MatchGate(settings.min_percent, settings.cooldown), store, dispatcher)
    svc = Services(settings, store, users, handler.gate, dispatcher, hub)

    engine = sync = None
    if settings.ai_enabled:
        from main import AIVisionPipeline      # first: it adds the us-* folders to sys.path
        from face_engine import FaceEngine
        pipeline = AIVisionPipeline(
            source=settings.camera_source, camera_id=settings.camera_id,
            store_path=str(settings.data_dir / "references.npz"),
            evidence_dir=str(settings.data_dir / "evidence"),
            alert_cooldown=settings.cooldown, on_match=handler)
        engine = Engine(pipeline)
        if settings.supabase_url and settings.supabase_key:
            sync = PersonSync(settings, pipeline, pipeline.store, FaceEngine())
            engine.sync = sync
        svc.engine = engine
        svc.persons = sync.persons if sync else (
            lambda: [{"id": i, "name": p["name"]} for i, p in pipeline.store.persons.items()])
    return create_app(svc), engine, sync


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = Settings.from_env()
    app, engine, sync = build(settings)
    if engine:
        engine.start()
    if sync:
        sync.start()
    log.info("serving on http://%s:%s (AI %s, Supabase sync %s)", settings.host, settings.port,
             "on" if engine else "off", "on" if sync else "off")
    uvicorn.run(app, host=settings.host, port=settings.port, log_level="warning", access_log=False)


if __name__ == "__main__":
    main()
