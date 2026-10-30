"""P1.2: match verification gate (Module 3).

The AI already confirms a match over several frames (3 of 5). This is the second,
independent check before an operator is alerted: the result must be well formed, strong
enough, and not a repeat of a recent alert for the same person.
"""

import threading
import time

REQUIRED = ("person_id", "name", "confidence_percent", "camera_id", "timestamp", "scene_image")


class MatchGate:

    def __init__(self, min_percent=55.0, cooldown=30.0, clock=time.monotonic):
        # 55 % is the mapped value of the AI's own confirmation bar (mean cosine 0.40).
        self.min_percent, self.cooldown, self.clock = min_percent, cooldown, clock
        self.last = {}                    # person_id -> time of last accepted alert
        self.lock = threading.Lock()

    def check(self, result):
        """Returns (accepted, reason). Accepting records the alert time for the cooldown."""
        missing = [k for k in REQUIRED if result.get(k) in (None, "")]
        if missing:
            return False, f"malformed: missing {', '.join(missing)}"

        try:
            percent = float(result["confidence_percent"])
        except (TypeError, ValueError):
            return False, "malformed: confidence_percent is not a number"
        if percent < self.min_percent:
            return False, f"below threshold: {percent} < {self.min_percent}"

        now, person = self.clock(), result["person_id"]
        with self.lock:
            seen = self.last.get(person)
            if seen is not None and now - seen < self.cooldown:
                return False, f"cooldown: {person} alerted {now - seen:.0f}s ago"
            self.last[person] = now
        return True, "ok"
