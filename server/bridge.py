"""P3: connects Module 2 (AI vision) to Module 3 (alerts) and to the Supabase persons table."""

import logging
import threading
import time

import cv2
import httpx
import numpy as np

log = logging.getLogger("rtvis.bridge")
logging.getLogger("httpx").setLevel(logging.WARNING)     # request URLs can carry keys


# ---------------------------------------------------------------- match -> alert
class MatchHandler:
    """The AI's on_match callback: gate -> store -> dispatch. Never raises into the AI thread."""

    def __init__(self, gate, store, dispatcher):
        self.gate, self.store, self.dispatcher = gate, store, dispatcher

    def __call__(self, result):
        ok, reason = self.gate.check(result)
        if not ok:
            log.info("match dropped: %s", reason)
            return None
        row = self.store.add(
            person_id=result["person_id"], person_name=result["name"], detected_at=result["timestamp"],
            confidence=float(result["confidence_percent"]), camera=result["camera_id"],
            track_id=result.get("track_id"), zone=(result.get("location") or {}).get("zone"),
            verified_frames=result.get("verified_frames"),
            scene_path=result["scene_image"], face_path=result.get("face_image"))
        self.dispatcher.dispatch(row)
        return row


# ---------------------------------------------------------------- AI pipeline in a thread
class Engine:
    """Runs AIVisionPipeline headless in a thread; serves its latest annotated frame and status."""

    def __init__(self, pipeline):
        self.pipeline = pipeline
        pipeline.on_frame = self._on_frame
        self.thread = None
        self._view, self._seq, self._jpeg, self._jpeg_seq = None, 0, None, -1
        self.last_frame_at = 0.0
        self.sync = None                          # PersonSync, set by the launcher

    def start(self):
        self.thread = threading.Thread(target=self._run, name="ai-pipeline", daemon=True)
        self.thread.start()

    def stop(self):
        self.pipeline.stop_event.set()

    def _run(self):
        try:
            self.pipeline.run(display=False)
        except Exception:
            log.exception("AI pipeline crashed")

    def _on_frame(self, view):
        self._view, self._seq, self.last_frame_at = view, self._seq + 1, time.time()

    def latest_jpeg(self):
        """Encode lazily: the stream polls at 10 Hz, the AI may run faster."""
        if self._view is not None and self._seq != self._jpeg_seq:
            ok, buf = cv2.imencode(".jpg", self._view, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                self._jpeg, self._jpeg_seq = buf.tobytes(), self._seq
        return self._jpeg

    def status(self):
        alive = bool(self.thread and self.thread.is_alive())
        fresh = time.time() - self.last_frame_at < 5
        out = {"monitoring": "active" if alive and fresh else "idle" if alive else "offline",
               "activeCamera": self.pipeline.camera_id if alive else None,
               "aiService": "up" if alive else "down"}
        if self.sync:
            out["personSync"] = self.sync.state()
        return out


# ---------------------------------------------------------------- Supabase persons -> reference store
class PersonSync:
    """Copies registered persons from Supabase into the AI's reference store, without a restart.

    Embeddings are computed with a private FaceEngine (OpenCV DNN objects are not thread-safe) and the
    pipeline's store is replaced in one assignment, so the AI thread never sees a half-updated store.
    """

    def __init__(self, settings, pipeline, base_store, engine, client=None):
        self.s, self.pipeline, self.base, self.engine = settings, pipeline, base_store, engine
        self.http = client or httpx.Client(timeout=10)
        self.known = {}                           # person id -> {"name", "photo", "emb"}
        self.failed = {}                          # person id -> photo path that could not be used
        self.last_error, self.last_ok, self.stop_event = None, None, threading.Event()

    # -- supabase REST --
    def _headers(self):
        return {"apikey": self.s.supabase_key, "Authorization": f"Bearer {self.s.supabase_key}"}

    def fetch_rows(self):
        r = self.http.get(f"{self.s.supabase_url}/rest/v1/{self.s.supabase_table}",
                          params={"select": "id,name,photo_path"}, headers=self._headers())
        r.raise_for_status()
        return r.json()

    def fetch_photo(self, path):
        base = f"{self.s.supabase_url}/storage/v1/object"
        r = self.http.get(f"{base}/authenticated/{self.s.supabase_bucket}/{path}", headers=self._headers())
        if r.status_code in (400, 401, 403, 404):            # public bucket: no auth route
            r = self.http.get(f"{base}/public/{self.s.supabase_bucket}/{path}")
        r.raise_for_status()
        return r.content

    # -- sync --
    def sync_once(self):
        """Returns {"added": [...], "removed": [...], "failed": [...]}."""
        try:
            rows = self.fetch_rows()
        except (httpx.HTTPError, ValueError) as error:
            self.last_error = f"{type(error).__name__}"       # no URL/key in the message
            log.warning("person sync: Supabase unreachable (%s)", self.last_error)
            return {"added": [], "removed": [], "failed": [], "error": self.last_error}

        live = {str(r["id"]): r for r in rows}
        removed = [pid for pid in self.known if pid not in live]
        for pid in removed:
            del self.known[pid]
        added, failed = [], []
        for pid, row in live.items():
            photo = row.get("photo_path")
            current = self.known.get(pid)
            if (current and current["photo"] == photo) or self.failed.get(pid) == photo or not photo:
                if current and current["name"] != row["name"]:
                    current["name"] = row["name"]
                    added.append(pid)
                continue
            try:
                self.known[pid] = {"name": row["name"], "photo": photo, "emb": self._embed(self.fetch_photo(photo))}
                self.failed.pop(pid, None)
                added.append(pid)
            except httpx.HTTPError as error:
                log.warning("person sync: photo download failed for %s (%s)", pid, type(error).__name__)
                failed.append(pid)                             # retried next round
            except ValueError as error:                        # unreadable image / no face: do not retry
                log.warning("person sync: %s unusable: %s", pid, error)
                self.failed[pid] = photo
                failed.append(pid)

        self.last_error, self.last_ok = None, time.time()
        if added or removed:
            self._swap()
        return {"added": added, "removed": removed, "failed": failed}

    def _embed(self, data):
        image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("not an image")
        aligned, _ = self._reference.aligned_from_image(image)
        return np.vstack([self.engine.embed_aligned(aligned), self.engine.embed_aligned(cv2.flip(aligned, 1))])

    @property
    def _reference(self):
        from reference_store import ReferenceStore
        if not hasattr(self, "_ref"):
            self._ref = ReferenceStore(path=None, engine=self.engine)
        return self._ref

    def _swap(self):
        from reference_store import ReferenceStore
        merged = ReferenceStore(path=None)
        merged.person_ids = list(self.base.person_ids)
        merged.persons = dict(self.base.persons)
        chunks = [self.base.embeddings]
        for pid, p in self.known.items():
            merged.person_ids += [pid] * len(p["emb"])
            merged.persons[pid] = {"name": p["name"], "photos": [p["photo"]]}
            chunks.append(p["emb"])
        merged.embeddings = np.vstack(chunks).astype(np.float32)
        self.pipeline.store = merged                           # single assignment = atomic for the AI thread

    # -- API helpers --
    def persons(self):
        names = {pid: p["name"] for pid, p in self.base.persons.items()}
        names.update({pid: p["name"] for pid, p in self.known.items()})
        return [{"id": pid, "name": name} for pid, name in names.items()]

    def state(self):
        return {"ok": self.last_error is None and self.last_ok is not None, "error": self.last_error,
                "lastSync": self.last_ok, "persons": len(self.known)}

    def run(self):
        while not self.stop_event.is_set():
            self.sync_once()
            self.stop_event.wait(self.s.sync_interval)

    def start(self):
        threading.Thread(target=self.run, name="person-sync", daemon=True).start()
