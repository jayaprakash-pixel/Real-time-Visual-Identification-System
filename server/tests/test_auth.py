import time

from auth import AuthError
import pytest


def test_signup_login_flow(client):
    r = client.post("/api/auth/signup", json={"name": "Op", "email": "Op@Example.com", "password": "password123"})
    assert r.status_code == 200
    body = r.json()
    assert body["user"] == {"name": "Op", "email": "op@example.com", "role": "Admin"}   # first account bootstraps
    assert client.post("/api/auth/login", json={"email": "op@example.com", "password": "password123"}).status_code == 200


def test_duplicate_409_and_bad_password_401(client, token):
    r = client.post("/api/auth/signup", json={"name": "x", "email": "op@example.com", "password": "password123"})
    assert r.status_code in (403, 409)
    r = client.post("/api/auth/login", json={"email": "op@example.com", "password": "wrong-password"})
    assert r.status_code == 401 and r.json()["message"] == "Invalid email or password."
    assert client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "x"}).status_code == 401


def test_duplicate_email_is_409_when_signup_open(svc, client, token):
    svc.users.allow_signup = True
    r = client.post("/api/auth/signup", json={"name": "x", "email": "op@example.com", "password": "password123"})
    assert r.status_code == 409 and r.json()["field"] == "email"


def test_second_signup_closed_by_default(client, token):
    r = client.post("/api/auth/signup", json={"name": "y", "email": "two@example.com", "password": "password123"})
    assert r.status_code == 403


def test_short_password_rejected(client):
    r = client.post("/api/auth/signup", json={"name": "x", "email": "a@b.co", "password": "short"})
    assert r.status_code == 400 and r.json()["field"] == "password"


def test_protected_routes_need_token(client, auth):
    for path in ("/api/system/status", "/api/detections", "/api/detections/count", "/api/persons"):
        assert client.get(path).status_code == 401, path
        assert client.get(path, headers={"Authorization": "Bearer junk"}).status_code == 401, path
        assert client.get(path, headers=auth).status_code == 200, path
    assert client.get("/health").status_code == 200


def test_tampered_and_expired_tokens(svc, token):
    body, sig = token.split(".")
    with pytest.raises(AuthError):
        svc.users.verify(f"{body}.{'0' * len(sig)}")
    with pytest.raises(AuthError):
        svc.users.verify(svc.users.issue("op@example.com", ttl=-1))


def test_media_token_cannot_call_api(client, svc, token):
    media = svc.users.issue("op@example.com", ttl=60, scope="media")
    assert client.get("/api/detections", headers={"Authorization": f"Bearer {media}"}).status_code == 401
    assert client.get(f"/api/system/status?token={media}").status_code == 401
