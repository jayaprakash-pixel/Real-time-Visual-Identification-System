import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import Services, create_app
from auth import Users
from config import Settings
from dispatch import Dispatcher
from gate import MatchGate
from hub import Hub
from store import Store


def jpeg(color=(40, 60, 200)):
    ok, buf = cv2.imencode(".jpg", np.full((48, 64, 3), color, np.uint8))
    return buf.tobytes()


class FakeEngine:
    def __init__(self):
        self.frame = jpeg()

    def latest_jpeg(self):
        return self.frame

    def status(self):
        return {"monitoring": "active", "activeCamera": "CAM01", "aiService": "up"}


@pytest.fixture
def svc(tmp_path):
    s = Settings(data_dir=tmp_path, frontend_dist=tmp_path / "no-dist", allow_signup=False)
    store, hub, dispatcher = Store(), Hub(), Dispatcher()
    users = Users(store.db, store.lock, b"test-secret", allow_signup=False)
    dispatcher.add("websocket", hub.broadcast)
    return Services(s, store, users, MatchGate(), dispatcher, hub, FakeEngine(),
                    persons=lambda: [{"id": "p1", "name": "Asha", "extra": "x"}, {"id": "p2", "name": "Ravi"}])


@pytest.fixture
def client(svc):
    with TestClient(create_app(svc)) as c:
        yield c


@pytest.fixture
def token(client):
    r = client.post("/api/auth/signup", json={"name": "Op", "email": "op@example.com", "password": "password123"})
    assert r.status_code == 200
    return r.json()["token"]


@pytest.fixture
def auth(token):
    return {"Authorization": f"Bearer {token}"}


def add_detection(svc, tmp_path, i=0, person="p1", name="Asha"):
    scene = tmp_path / f"scene{i}.jpg"
    scene.write_bytes(jpeg())
    return svc.store.add(person_id=person, person_name=name, detected_at=f"2026-10-30T12:00:{i:02d}",
                         confidence=80 + i, camera="CAM01", scene_path=str(scene), face_path=None)
