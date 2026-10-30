"""P1.1: SQLite store for accepted detections (one row per alert)."""

import sqlite3
import threading
import uuid

COLUMNS = ("id", "person_id", "person_name", "detected_at", "confidence", "camera",
           "track_id", "zone", "verified_frames", "scene_path", "face_path")

SORTABLE = {"detectedAt": "detected_at", "confidence": "confidence", "personName": "person_name"}


class Store:

    def __init__(self, path=":memory:"):
        # One connection shared by the AI thread and web threads; the lock serialises use.
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.lock, self.db:
            self.db.execute(f"""CREATE TABLE IF NOT EXISTS detections (
                id TEXT PRIMARY KEY, person_id TEXT NOT NULL, person_name TEXT NOT NULL,
                detected_at TEXT NOT NULL, confidence REAL NOT NULL, camera TEXT NOT NULL,
                track_id INTEGER, zone TEXT, verified_frames INTEGER,
                scene_path TEXT, face_path TEXT)""")
            self.db.execute("CREATE INDEX IF NOT EXISTS ix_det_time ON detections(detected_at)")

    def add(self, **fields):
        """Insert one detection. Unknown keys are rejected so typos fail loudly."""
        row = {c: fields.pop(c, None) for c in COLUMNS}
        if fields:
            raise TypeError(f"unknown detection fields: {sorted(fields)}")
        row["id"] = row["id"] or uuid.uuid4().hex
        with self.lock, self.db:
            self.db.execute(
                f"INSERT INTO detections ({','.join(COLUMNS)}) VALUES ({','.join('?' * len(COLUMNS))})",
                [row[c] for c in COLUMNS])
        return row

    def get(self, detection_id):
        with self.lock:
            r = self.db.execute("SELECT * FROM detections WHERE id=?", (detection_id,)).fetchone()
        return dict(r) if r else None

    def count(self):
        with self.lock:
            return self.db.execute("SELECT COUNT(*) FROM detections").fetchone()[0]

    def list(self, person=None, camera=None, date_from=None, date_to=None,
             confidence_min=None, confidence_max=None,
             sort_by="detectedAt", sort_order="desc", page=1, page_size=10):
        """Returns (items, total). `person` matches an id exactly or a name substring."""
        where, args = [], []
        if person:
            where.append("(person_id = ? OR person_name LIKE ?)")
            args += [person, f"%{person}%"]
        if camera:
            where.append("camera = ?")
            args.append(camera)
        if date_from:
            where.append("detected_at >= ?")
            args.append(f"{date_from}T00:00:00")
        if date_to:
            where.append("detected_at <= ?")
            args.append(f"{date_to}T23:59:59.999999")
        if confidence_min is not None:
            where.append("confidence >= ?")
            args.append(float(confidence_min))
        if confidence_max is not None:
            where.append("confidence <= ?")
            args.append(float(confidence_max))

        clause = ("WHERE " + " AND ".join(where)) if where else ""
        column = SORTABLE.get(sort_by, "detected_at")          # whitelist: never interpolate input
        direction = "ASC" if sort_order == "asc" else "DESC"
        page, page_size = max(1, int(page)), max(1, min(200, int(page_size)))

        with self.lock:
            total = self.db.execute(f"SELECT COUNT(*) FROM detections {clause}", args).fetchone()[0]
            rows = self.db.execute(
                f"SELECT * FROM detections {clause} ORDER BY {column} {direction}, id LIMIT ? OFFSET ?",
                args + [page_size, (page - 1) * page_size]).fetchall()
        return [dict(r) for r in rows], total
