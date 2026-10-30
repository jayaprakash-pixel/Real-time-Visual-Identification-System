"""P1.3: alert dispatcher. Fans one alert out to every channel; a failing channel never blocks the rest."""

import logging

log = logging.getLogger("rtvis.dispatch")


class Dispatcher:

    def __init__(self):
        self.channels = []                # (name, callable(alert))

    def add(self, name, send):
        self.channels.append((name, send))

    def dispatch(self, alert):
        """Returns {channel: "ok" | error text}."""
        outcome = {}
        for name, send in self.channels:
            try:
                send(alert)
                outcome[name] = "ok"
            except Exception as error:    # isolation is the point: log and carry on
                log.error("alert channel %s failed: %s", name, error)
                outcome[name] = f"{type(error).__name__}: {error}"
        return outcome
