"""P1.4: optional Telegram channel. Off unless a bot token and chat id are configured."""

import logging

import httpx

log = logging.getLogger("rtvis.telegram")

# httpx logs every request URL at INFO, and a Telegram URL contains the bot token.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class Telegram:

    def __init__(self, token, chat_id, api="https://api.telegram.org", timeout=5.0):
        self.token, self.chat_id, self.api, self.timeout = token, chat_id, api.rstrip("/"), timeout

    @property
    def enabled(self):
        return bool(self.token and self.chat_id)

    def __call__(self, alert):
        if not self.enabled:
            return
        text = (f"MATCH: {alert['personName']} ({alert['confidence']}%)\n"
                f"Camera: {alert['cameraSource']}\nTime: {alert['detectedAt']}")
        try:
            r = httpx.post(f"{self.api}/bot{self.token}/sendMessage",
                           json={"chat_id": self.chat_id, "text": text}, timeout=self.timeout)
            r.raise_for_status()
        except httpx.HTTPError as error:
            # httpx puts the URL (which holds the token) in its messages: never log it.
            raise RuntimeError(f"telegram send failed ({type(error).__name__})") from None
