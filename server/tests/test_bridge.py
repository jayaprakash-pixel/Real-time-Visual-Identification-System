from bridge import Engine, MatchHandler
from conftest import jpeg
from starlette.testclient import TestClient  # noqa: F401  (fixtures use it)


def ai_result(**over):
    r = {"person_id": "MP001", "name": "Asha", "confidence": 0.55, "confidence_percent": 87.0,
         "verified_frames": 3, "camera_id": "PHONE1", "track_id": 4,
         "location": {"zone": "top-center", "bbox": [1, 2, 3, 4]}, "match": True,
         "timestamp": "2026-10-30T12:00:00", "scene_image": "scene.jpg", "face_image": "face.jpg"}
    r.update(over)
    return r


def test_result_goes_through_gate_store_and_websocket(svc, client, token):
    handler = MatchHandler(svc.gate, svc.store, svc.dispatcher)
    with client.websocket_connect(f"/alerts?token={token}") as ws:
        row = handler(ai_result())
        msg = ws.receive_json()
        assert svc.store.count() == 1
        assert row["zone"] == "top-center" and row["verified_frames"] == 3
        assert msg["personName"] == "Asha" and msg["cameraSource"] == "PHONE1" and msg["confidence"] == 87.0

        # same person again inside the cooldown: dropped, nothing stored or sent
        assert handler(ai_result(timestamp="2026-10-30T12:00:05")) is None
        assert svc.store.count() == 1


def test_weak_or_malformed_results_are_dropped(svc):
    handler = MatchHandler(svc.gate, svc.store, svc.dispatcher)
    assert handler(ai_result(confidence_percent=20)) is None
    assert handler(ai_result(scene_image=None)) is None
    assert svc.store.count() == 0


def test_dispatch_failure_does_not_break_the_ai_callback(svc):
    svc.dispatcher.add("broken", lambda a: 1 / 0)
    handler = MatchHandler(svc.gate, svc.store, svc.dispatcher)
    assert handler(ai_result()) is not None and svc.store.count() == 1


def test_engine_serves_latest_frame_and_status():
    class P:
        camera_id = "CAM9"
        on_frame = None
    import numpy as np
    e = Engine(P())
    assert e.latest_jpeg() is None and e.status()["aiService"] == "down" and e.status()["monitoring"] == "offline"
    e._on_frame(np.full((48, 64, 3), 90, np.uint8))
    assert e.latest_jpeg()[:2] == b"\xff\xd8"
    first = e.latest_jpeg()
    assert e.latest_jpeg() is first                      # cached until a new frame arrives
