"""
US-08: Multi-frame match verification.

A single frame never produces a match. Each tracked face (US-03 track ID)
keeps its last few recognition results; a match is CONFIRMED only when the
same person wins enough of them with a good average score.

    Track #7:  MP002 0.52 | MP002 0.48 | none 0.20 | MP002 0.55
               -> 3 of last 5 agree on MP002, mean 0.52 -> CONFIRMED MP002
"""

from collections import deque


class MatchVerifier:

    def __init__(self, window=5, required_hits=3, min_mean_score=0.40):
        self.window = window
        self.required_hits = required_hits
        self.min_mean_score = min_mean_score

        self.history = {}     # track_id -> deque of (person_id | None, score)
        self.confirmed = {}   # track_id -> person_id

    def update(self, track_id, decision):
        """
        decision: output of match_decision.decide

        Returns the confirmed result the FIRST time a track is confirmed:
            {"person_id": str, "score": float (mean of agreeing frames), "hits": int}
        otherwise None.
        """
        history = self.history.setdefault(track_id, deque(maxlen=self.window))
        history.append((decision["person_id"], decision["score"]))

        if track_id in self.confirmed:
            return None

        person_id = decision["person_id"]

        if person_id is None:
            return None

        scores = [score for pid, score in history if pid == person_id]
        mean_score = sum(scores) / len(scores)

        if len(scores) >= self.required_hits and mean_score >= self.min_mean_score:
            self.confirmed[track_id] = person_id
            return {"person_id": person_id, "score": mean_score, "hits": len(scores)}

        return None

    def is_pending(self, track_id):
        """True when a track has a possible (unconfirmed) match being verified."""
        return track_id not in self.confirmed and any(
            pid is not None for pid, _ in self.history.get(track_id, ())
        )

    def status(self, track_id):
        """(state, person_id) for display: 'confirmed' | 'verifying' | 'unknown'."""
        if track_id in self.confirmed:
            return "confirmed", self.confirmed[track_id]

        history = self.history.get(track_id)

        if history and history[-1][0] is not None:
            return "verifying", history[-1][0]

        return "unknown", None

    def retain(self, active_track_ids):
        """Forget tracks the tracker has dropped."""
        for track_id in list(self.history):
            if track_id not in active_track_ids:
                self.history.pop(track_id, None)
                self.confirmed.pop(track_id, None)


if __name__ == "__main__":
    # Self-check: one lucky frame must not confirm; consistent frames must.
    verifier = MatchVerifier()

    match = lambda pid, s: {"match": True, "person_id": pid, "score": s}
    no_match = {"match": False, "person_id": None, "score": 0.1}

    assert verifier.update(1, match("MP001", 0.9)) is None
    assert verifier.update(1, no_match) is None
    assert verifier.update(1, match("MP001", 0.5)) is None
    assert verifier.is_pending(1)
    result = verifier.update(1, match("MP001", 0.5))
    assert result and result["person_id"] == "MP001" and result["hits"] == 3
    assert verifier.update(1, match("MP001", 0.6)) is None     # confirmed only once
    assert verifier.status(1) == ("confirmed", "MP001")

    # Weak scores: 3 hits but mean below 0.40 -> not confirmed
    for s in (0.37, 0.38, 0.37):
        assert verifier.update(2, match("MP002", s)) is None

    # Flicker between two people -> not confirmed
    for pid in ("MP001", "MP002", "MP001", "MP002"):
        assert verifier.update(3, match(pid, 0.6)) is None

    verifier.retain({1})
    assert 2 not in verifier.history and verifier.status(1)[0] == "confirmed"

    print("US-08 match verifier: all checks passed")
