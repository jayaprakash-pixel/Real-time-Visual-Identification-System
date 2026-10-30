"""P5.4: one test per line of docs/security.md."""

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.routing import WebSocketRoute
from starlette.websockets import WebSocketDisconnect

from app import create_app

OPEN = {"/health", "/api/auth/login", "/api/auth/signup"}


def test_every_route_except_the_open_ones_rejects_anonymous_callers(svc):
    app = create_app(svc)
    checked = 0
    with TestClient(app) as c:
        for r in app.routes:
            path = getattr(r, "path", "")
            if path in OPEN or not isinstance(r, (APIRoute, WebSocketRoute)):
                continue
            url = path.replace("{detection_id}", "x").replace("{kind}", "scene")
            if isinstance(r, WebSocketRoute):
                with pytest.raises(WebSocketDisconnect):
                    with c.websocket_connect(url):
                        pass
            else:
                assert c.get(url).status_code == 401, path
            checked += 1
    assert checked >= 7                                  # detections x3, count, persons, status, stream, alerts


def test_login_is_throttled_after_five_failures(client, token):
    for _ in range(5):
        assert client.post("/api/auth/login", json={"email": "op@example.com", "password": "bad-password"}).status_code == 401
    r = client.post("/api/auth/login", json={"email": "op@example.com", "password": "password123"})
    assert r.status_code == 429                          # even the right password is refused during the lock


def test_cors_only_for_listed_origins(client):
    ok = client.get("/health", headers={"Origin": "http://localhost:5173"})
    bad = client.get("/health", headers={"Origin": "https://evil.example"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in bad.headers


def test_evidence_route_cannot_be_pointed_at_other_files(client, auth):
    for evil in ("..%2f..%2fsecret.key", "%2e%2e%2fserver.db", "../../.env"):
        assert client.get(f"/api/detections/{evil}/scene", headers=auth).status_code in (404, 405)


def test_static_fallback_cannot_escape_the_build_folder(svc, tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>app</html>")
    (tmp_path / "secret.txt").write_text("TOP SECRET")
    svc.settings.frontend_dist = dist
    with TestClient(create_app(svc)) as c:
        assert "app" in c.get("/anything").text
        for evil in ("../secret.txt", "..%2fsecret.txt", "%2e%2e/secret.txt"):
            assert "TOP SECRET" not in c.get("/" + evil).text


def test_status_never_contains_secrets(svc, client, auth):
    svc.settings.supabase_key = "SUPERSECRETKEY"
    svc.settings.telegram_token = "BOTTOKEN"
    body = client.get("/api/system/status", headers=auth).text
    assert "SUPERSECRETKEY" not in body and "BOTTOKEN" not in body


def test_passwords_are_not_stored_in_clear(svc, token):
    row = svc.store.db.execute("SELECT * FROM users").fetchone()
    assert "password123" not in str(dict(row)) and len(row["hash"]) == 128 and len(row["salt"]) == 16
