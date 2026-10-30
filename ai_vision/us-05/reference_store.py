"""
US-05: Missing-person reference management.

Reference photos are turned into embeddings ONCE (at registration) and kept
in memory, so the live pipeline never re-processes the photos per frame.

Member 1's registration module calls ReferenceStore.add(...) after saving a
case. For manual use / demos there is a small CLI:

    python reference_store.py capture MP001 "Rahul Kumar"      (from webcam)
    python reference_store.py add MP001 "Rahul Kumar" photo1.jpg photo2.jpg
    python reference_store.py list
    python reference_store.py remove MP001
"""

import json
import os
import sys

import cv2
import numpy as np

AI_VISION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(AI_VISION_DIR, "us-02"))

from face_engine import FaceEngine


DEFAULT_STORE = os.path.join(AI_VISION_DIR, "data", "references.npz")


class ReferenceStore:

    def __init__(self, path=DEFAULT_STORE, engine=None):
        self.path = path
        self.engine = engine
        self.person_ids = []      # one entry per embedding (a person may have several photos)
        self.embeddings = np.zeros((0, 128), dtype=np.float32)
        self.persons = {}         # person_id -> {"name": ..., "photos": [...]}

        # path=None -> temporary in-memory store (used by test scripts)
        if path and os.path.exists(path):
            self.load()

    # ---------------------------------------------------------
    # Load / save
    # ---------------------------------------------------------

    def load(self):
        data = np.load(self.path, allow_pickle=False)
        self.person_ids = [str(p) for p in data["person_ids"]]
        self.embeddings = data["embeddings"].astype(np.float32)
        self.persons = json.loads(str(data["persons"]))

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

        # Write then rename, so a crash never leaves a half-written store.
        tmp_path = self.path + ".tmp.npz"
        np.savez(
            tmp_path,
            person_ids=np.array(self.person_ids, dtype=str),
            embeddings=self.embeddings,
            persons=json.dumps(self.persons),
        )
        os.replace(tmp_path, self.path)

    # ---------------------------------------------------------
    # Enrolment
    # ---------------------------------------------------------

    def aligned_from_image(self, image):
        """
        Reference photo -> aligned 112x112 face.
        image: BGR array or path. Uses the largest face in the photo.
        """
        if isinstance(image, str):
            path = image
            image = cv2.imread(path)

            if image is None:
                raise ValueError(f"Could not read image: {path}")

        if self.engine is None:
            self.engine = FaceEngine()

        faces = self.engine.detect(image)

        if not faces:
            raise ValueError("No face found in the reference photo")

        face = max(faces, key=lambda f: f["bbox"][2] * f["bbox"][3])
        aligned = self.engine.align(image, face)

        if aligned is None:
            raise ValueError("Could not align the face in the reference photo")

        return aligned, len(faces)

    def embedding_from_image(self, image):
        aligned, face_count = self.aligned_from_image(image)
        return self.engine.embed_aligned(aligned), face_count

    def add(self, person_id, name, images, details=None):
        """
        Register (or add more photos to) a missing person.

        images:  list of BGR arrays or file paths (more photos = better recall)
        details: optional dict from Member 1 (age, gender, missing date...)

        Returns the number of photos added.
        """
        person_id = str(person_id).strip()

        if not person_id:
            raise ValueError("person_id is required")

        if isinstance(images, (str, np.ndarray)):
            images = [images]

        new_embeddings = []
        photo_names = []

        for image in images:
            aligned, face_count = self.aligned_from_image(image)

            if face_count > 1:
                print(f"Warning: {face_count} faces in photo for {person_id}; using the largest.")

            # Also store the mirror image: a photo of the face turned left
            # then also covers the face turned right.
            new_embeddings.append(self.engine.embed_aligned(aligned))
            new_embeddings.append(self.engine.embed_aligned(cv2.flip(aligned, 1)))
            photo_names.append(os.path.abspath(image) if isinstance(image, str) else "<array>")

        person = self.persons.setdefault(person_id, {"name": name, "photos": []})
        person["name"] = name
        person["photos"] += photo_names

        if details:
            person["details"] = details

        self.person_ids += [person_id] * len(new_embeddings)
        self.embeddings = np.vstack([self.embeddings, *new_embeddings]).astype(np.float32)

        if self.path:
            self.save()

        return len(photo_names)

    def remove(self, person_id):
        keep = [i for i, p in enumerate(self.person_ids) if p != person_id]
        self.person_ids = [self.person_ids[i] for i in keep]
        self.embeddings = self.embeddings[keep]
        removed = self.persons.pop(person_id, None) is not None

        if self.path:
            self.save()
        return removed

    def name_of(self, person_id):
        return self.persons.get(person_id, {}).get("name", person_id)

    def __len__(self):
        return len(self.persons)


# -------------------------------------------------------------
# CLI
# -------------------------------------------------------------

if __name__ == "__main__":
    args = sys.argv[1:]
    store = ReferenceStore()

    if len(args) >= 4 and args[0] == "add":
        count = store.add(args[1], args[2], args[3:])
        print(f"Added {count} photo(s) for {args[1]} ({args[2]})")

    elif args[:1] == ["list"]:
        print(f"{len(store)} registered person(s) in {store.path}")
        for pid, info in store.persons.items():
            count = store.person_ids.count(pid)
            print(f"  {pid:<10} {info['name']:<25} {count} embedding(s)")

    elif len(args) >= 3 and args[0] == "capture":
        # Register a face straight from the webcam (handy for testing).
        sys.path.append(os.path.join(AI_VISION_DIR, "us-01"))
        from camera_source import open_camera, read_frame, release_camera

        person_id, name = args[1], args[2]
        camera = open_camera(args[3] if len(args) > 3 else 0)
        store.engine = store.engine or FaceEngine()
        photos = []

        # Different angles make recognition work when the face is not frontal.
        poses = ["Look STRAIGHT", "Turn a little LEFT", "Turn a little RIGHT",
                 "Look a little UP", "Look a little DOWN"]

        print("Follow the instruction on screen, press SPACE for each pose (Q = stop early)")

        while len(photos) < len(poses):
            frame = read_frame(camera)
            if frame is None:
                break

            faces = store.engine.detect(frame)
            view = frame.copy()
            for face in faces:
                x, y, w, h = face["bbox"]
                cv2.rectangle(view, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(view, f"{len(photos) + 1}/{len(poses)}: {poses[len(photos)]}",
                        (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(view, "SPACE = capture   Q = stop",
                        (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow("Register face", view)

            key = cv2.waitKey(1) & 0xFF
            if key == ord(" "):
                if len(faces) == 1:
                    photos.append(frame.copy())
                    print(f"Captured: {poses[len(photos) - 1]}")
                else:
                    print(f"Need exactly 1 face in view (found {len(faces)})")
            elif key == ord("q"):
                break

        release_camera(camera)
        cv2.destroyAllWindows()

        if photos:
            count = store.add(person_id, name, photos)
            print(f"Registered {name} ({person_id}) with {count} photo(s)")
        else:
            print("No photos taken, nothing registered")

    elif len(args) == 2 and args[0] == "remove":
        print("Removed" if store.remove(args[1]) else "Not found", args[1])

    else:
        print(__doc__)
