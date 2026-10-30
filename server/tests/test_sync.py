"""P3.3 person sync against a fake Supabase. Needs real face photos, which are never committed:
set RTVIS_TEST_FACES to a folder with image_01.jpg + image_02.jpg (same person) and image_03.jpg (other)."""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import httpx
import pytest

FACES = os.environ.get("RTVIS_TEST_FACES")
pytestmark = pytest.mark.skipif(not FACES, reason="RTVIS_TEST_FACES not set")


@pytest.fixture
def supabase():
    state = {"rows": [], "files": {}, "down": False}

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            if state["down"]:
                self.send_response(503); self.end_headers(); return
            if self.path.startswith("/rest/v1/missing_persons"):
                assert self.headers["apikey"] == "KEY"
                body, ctype = json.dumps(state["rows"]).encode(), "application/json"
            elif self.path.startswith("/storage/v1/object/authenticated/person-photos/"):
                path = self.path.split("person-photos/", 1)[1]
                if path not in state["files"]:
                    self.send_response(404); self.end_headers(); return
                body, ctype = state["files"][path], "image/jpeg"
            else:
                self.send_response(404); self.end_headers(); return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    state["url"] = f"http://127.0.0.1:{srv.server_port}"
    yield state
    srv.shutdown()


@pytest.fixture
def sync(supabase):
    from bridge import PersonSync
    from config import Settings
    from face_engine import FaceEngine
    from reference_store import ReferenceStore

    class Pipe:
        store = ReferenceStore(path=None)

    engine = FaceEngine()
    s = Settings(supabase_url=supabase["url"], supabase_key="KEY")
    return PersonSync(s, Pipe, Pipe.store, engine, client=httpx.Client(timeout=5)), Pipe, engine


def photo(name):
    return (Path(FACES) / name).read_bytes()


def test_add_match_and_delete(supabase, sync):
    ps, pipe, engine = sync
    from face_matcher import compare
    from reference_store import ReferenceStore

    supabase["rows"] = [{"id": "uuid-1", "name": "Asha", "photo_path": "registrations/a.jpg"}]
    supabase["files"]["registrations/a.jpg"] = photo("image_02.jpg")
    out = ps.sync_once()
    assert out["added"] == ["uuid-1"] and len(pipe.store) == 1
    assert ps.persons() == [{"id": "uuid-1", "name": "Asha"}]

    # the hot-swapped store really recognises the same person from a different photo
    probe = ReferenceStore(path=None, engine=engine).embedding_from_image(
        __import__("cv2").imread(str(Path(FACES) / "image_01.jpg")))[0]
    best_id, best = compare(probe, pipe.store)[0]
    assert best_id == "uuid-1" and best > 0.363

    assert ps.sync_once() == {"added": [], "removed": [], "failed": []}      # idempotent

    supabase["rows"] = []
    assert ps.sync_once()["removed"] == ["uuid-1"] and len(pipe.store) == 0


def test_unusable_photo_not_retried_and_does_not_block_others(supabase, sync):
    ps, pipe, _ = sync
    supabase["rows"] = [{"id": "bad", "name": "NoFace", "photo_path": "x/bad.jpg"},
                        {"id": "ok", "name": "Ravi", "photo_path": "x/ok.jpg"}]
    supabase["files"] = {"x/bad.jpg": b"not an image", "x/ok.jpg": photo("image_03.jpg")}
    out = ps.sync_once()
    assert out["added"] == ["ok"] and out["failed"] == ["bad"]
    assert ps.sync_once()["failed"] == []                                  # same bad photo: skipped


def test_supabase_down_keeps_last_known_persons(supabase, sync):
    ps, pipe, _ = sync
    supabase["rows"] = [{"id": "p", "name": "Asha", "photo_path": "x/a.jpg"}]
    supabase["files"]["x/a.jpg"] = photo("image_02.jpg")
    ps.sync_once()
    supabase["down"] = True
    out = ps.sync_once()
    assert "error" in out and len(pipe.store) == 1 and ps.state()["ok"] is False
    assert "KEY" not in str(ps.state()) and supabase["url"] not in str(ps.state())
    supabase["down"] = False
    ps.sync_once()
    assert ps.state()["ok"] is True
