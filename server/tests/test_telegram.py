import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from telegram import Telegram

ALERT = {"personName": "Asha", "confidence": 88.0, "cameraSource": "PHONE1", "detectedAt": "2026-10-30T12:00:00"}


@pytest.fixture
def fake_api():
    seen, mode = [], {"status": 200}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            body = self.rfile.read(int(self.headers["Content-Length"]))
            seen.append((self.path, json.loads(body)))
            self.send_response(mode["status"])
            self.end_headers()

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}", seen, mode
    srv.shutdown()


def test_sends_when_enabled(fake_api):
    url, seen, _ = fake_api
    Telegram("TOKEN123", "42", api=url)(ALERT)
    assert len(seen) == 1 and seen[0][0] == "/botTOKEN123/sendMessage"
    assert "Asha" in seen[0][1]["text"] and seen[0][1]["chat_id"] == "42"


def test_silent_when_disabled(fake_api):
    url, seen, _ = fake_api
    Telegram("", "", api=url)(ALERT)
    Telegram("TOKEN123", "", api=url)(ALERT)
    assert seen == []


def test_token_never_in_error_or_logs(fake_api, caplog):
    url, _, mode = fake_api
    mode["status"] = 500
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(RuntimeError) as e:
            Telegram("SECRETTOKEN", "42", api=url)(ALERT)
    assert "SECRETTOKEN" not in str(e.value) and "SECRETTOKEN" not in caplog.text
