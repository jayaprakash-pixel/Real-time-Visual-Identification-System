"""P2.6: fan-out of alerts to connected WebSocket clients. Safe to call from any thread."""

import asyncio


class Hub:

    def __init__(self):
        self.loop = None                  # set when the server starts
        self.clients = set()              # asyncio.Queue per connected client

    def subscribe(self):
        q = asyncio.Queue(maxsize=100)
        self.clients.add(q)
        return q

    def unsubscribe(self, q):
        self.clients.discard(q)

    def broadcast(self, detection):
        """Called by the dispatcher from the AI thread."""
        if self.loop is None:
            return
        for q in list(self.clients):
            self.loop.call_soon_threadsafe(self._put, q, detection)

    @staticmethod
    def _put(q, item):
        if not q.full():                  # a stalled client must not grow memory without bound
            q.put_nowait(item)
