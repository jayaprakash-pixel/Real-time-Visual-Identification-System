import threading
import time

import httpx
import uvicorn

from app import create_app
from conftest import add_detection


def test_status_shape(client, auth):
    j = client.get("/api/system/status", headers=auth).json()
    assert j["monitoring"] == "active" and j["activeCamera"] == "CAM01" and j["aiService"] == "up"
    assert j["streamUrl"].startswith("/video/stream?token=")
    assert "supabase" not in str(j).lower()


def test_detections_contract_and_paging(svc, client, auth, tmp_path):
    for i in range(12):
        add_detection(svc, tmp_path, i)
    j = client.get("/api/detections?page=2&pageSize=5", headers=auth).json()
    assert (j["total"], j["page"], j["pageSize"], len(j["items"])) == (12, 2, 5, 5)
    item = j["items"][0]
    assert set(item) == {"id", "personId", "personName", "detectedAt", "confidence", "cameraSource",
                         "sceneImageUrl", "thumbnailUrl"}
    assert client.get("/api/detections/count", headers=auth).json() == {"count": 12}


def test_recent_limit_returns_bare_array(svc, client, auth, tmp_path):
    for i in range(6):
        add_detection(svc, tmp_path, i)
    j = client.get("/api/detections?limit=3&sortBy=detectedAt&sortOrder=desc", headers=auth).json()
    assert isinstance(j, list) and len(j) == 3
    assert j[0]["detectedAt"] > j[1]["detectedAt"]


def test_filters(svc, client, auth, tmp_path):
    add_detection(svc, tmp_path, 1, "p1", "Asha")
    add_detection(svc, tmp_path, 2, "p2", "Ravi")
    assert client.get("/api/detections?person=ravi", headers=auth).json()["total"] == 1
    assert client.get("/api/detections?dateFrom=2026-10-31", headers=auth).json()["total"] == 0


def test_evidence_image_served_with_media_token(svc, client, auth, tmp_path):
    row = add_detection(svc, tmp_path)
    url = client.get("/api/detections", headers=auth).json()["items"][0]["sceneImageUrl"]
    r = client.get(url)
    assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg" and r.content[:2] == b"\xff\xd8"
    assert client.get(f"/api/detections/{row['id']}/scene").status_code == 401
    assert client.get(f"/api/detections/{row['id']}/scene?token=junk").status_code == 401
    assert client.get("/api/detections/nope/scene", headers=auth).status_code == 404
    assert client.get(f"/api/detections/{row['id']}/secret", headers=auth).status_code == 404


def test_persons_fields(client, auth):
    assert client.get("/api/persons?fields=id,name", headers=auth).json() == [
        {"id": "p1", "name": "Asha"}, {"id": "p2", "name": "Ravi"}]
    assert client.get("/api/persons?fields=id", headers=auth).json() == [{"id": "p1"}, {"id": "p2"}]


def test_mjpeg_stream_yields_decodable_frames(svc, token):
    import cv2
    import numpy as np
    app = create_app(svc)
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    while not server.started:
        time.sleep(0.05)
    port = server.servers[0].sockets[0].getsockname()[1]
    media = svc.users.issue("op@example.com", ttl=60, scope="media")
    try:
        assert httpx.get(f"http://127.0.0.1:{port}/video/stream").status_code == 401
        with httpx.stream("GET", f"http://127.0.0.1:{port}/video/stream?token={media}", timeout=5) as r:
            assert r.headers["content-type"].startswith("multipart/x-mixed-replace")
            buf = b""
            for chunk in r.iter_bytes():
                buf += chunk
                if buf.count(b"--frame") >= 4:
                    break
        parts = [p for p in buf.split(b"--frame") if b"\xff\xd8" in p]
        assert len(parts) >= 3
        for p in parts[:3]:
            data = p[p.index(b"\xff\xd8"):p.rindex(b"\xff\xd9") + 2]
            assert cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR) is not None
    finally:
        server.should_exit = True
        t.join(5)
