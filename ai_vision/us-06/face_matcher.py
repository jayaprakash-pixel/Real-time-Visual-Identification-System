"""
US-06: Facial embedding comparison.

Compares one live embedding with every registered reference embedding using
cosine similarity. Embeddings are L2-normalised (FaceEngine), so cosine
similarity is a single matrix-vector product - fast enough for hundreds of
registered persons on every recognition.
"""

import numpy as np


def cosine_similarity(embedding1, embedding2):
    a = np.asarray(embedding1, dtype=np.float32).flatten()
    b = np.asarray(embedding2, dtype=np.float32).flatten()
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def compare(live_embedding, store):
    """
    Returns [(person_id, score), ...] best first, one entry per person
    (a person with several reference photos gets their best score).
    """
    if len(store.person_ids) == 0:
        return []

    scores = store.embeddings @ live_embedding

    best = {}
    for person_id, score in zip(store.person_ids, scores):
        if score > best.get(person_id, -1.0):
            best[person_id] = float(score)

    return sorted(best.items(), key=lambda item: item[1], reverse=True)
