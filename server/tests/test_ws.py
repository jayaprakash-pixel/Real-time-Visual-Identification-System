import time

import pytest
from starlette.websockets import WebSocketDisconnect

from conftest import add_detection


def test_alert_arrives_with_frontend_shape(svc, client, token, tmp_path):
    row = add_detection(svc, tmp_path)
    with client.websocket_connect(f"/alerts?token={token}") as ws:
        svc.dispatcher.dispatch(row)
        msg = ws.receive_json()
    assert msg["personName"] == "Asha" and msg["confidence"] == 80
    assert set(msg) >= {"id", "personId", "detectedAt", "cameraSource", "sceneImageUrl", "thumbnailUrl"}
    assert "token=" in msg["sceneImageUrl"]
    assert client.get(msg["sceneImageUrl"]).status_code == 200


def test_refused_without_or_with_bad_token(client):
    for url in ("/alerts", "/alerts?token=junk"):
        with pytest.raises(WebSocketDisconnect) as e:
            with client.websocket_connect(url):
                pass
        assert e.value.code == 4401


def test_two_clients_both_receive(svc, client, token, tmp_path):
    row = add_detection(svc, tmp_path)
    with client.websocket_connect(f"/alerts?token={token}") as a, client.websocket_connect(f"/alerts?token={token}") as b:
        svc.dispatcher.dispatch(row)
        assert a.receive_json()["id"] == b.receive_json()["id"] == row["id"]


def test_disconnect_unsubscribes(svc, client, token):
    with client.websocket_connect(f"/alerts?token={token}"):
        assert len(svc.hub.clients) == 1
    deadline = time.time() + 2
    while svc.hub.clients and time.time() < deadline:
        time.sleep(0.05)
    assert not svc.hub.clients
