"""
US-07: Match confidence evaluation.

Turns similarity scores into a match / no-match decision.

0.363 is the cosine threshold published with the SFace model (OpenCV Zoo);
tune it with your own photos:

    python match_decision.py same_person_a.jpg same_person_b.jpg
    python match_decision.py person_a.jpg different_person.jpg

Same-person pairs should score clearly above the threshold and
different-person pairs clearly below it.
"""

SFACE_COSINE_THRESHOLD = 0.363


def decide(ranked_scores, threshold=SFACE_COSINE_THRESHOLD):
    """
    ranked_scores: output of face_matcher.compare -> [(person_id, score), ...]

    Returns {"match": bool, "person_id": str | None, "score": float}
    """
    if not ranked_scores:
        return {"match": False, "person_id": None, "score": 0.0}

    person_id, score = ranked_scores[0]

    if score >= threshold:
        return {"match": True, "person_id": person_id, "score": score}

    return {"match": False, "person_id": None, "score": score}


def confidence_percent(score, threshold=SFACE_COSINE_THRESHOLD):
    """
    Human-readable confidence for the operator/alert (Member 3).
    Raw cosine scores look low to people (0.5 is already a strong SFace
    match), so map: threshold -> 50 %, 0.7 and above -> 100 %.
    """
    scaled = 50 + 50 * (score - threshold) / (0.7 - threshold)
    return round(max(0.0, min(100.0, scaled)), 1)


if __name__ == "__main__":
    import os
    import sys

    AI_VISION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(AI_VISION_DIR, "us-05"))
    sys.path.append(os.path.join(AI_VISION_DIR, "us-06"))

    from reference_store import ReferenceStore
    from face_matcher import cosine_similarity

    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    # Temporary in-memory store: only used to reuse the enrolment code path.
    store = ReferenceStore(path=None)
    a, _ = store.embedding_from_image(sys.argv[1])
    b, _ = store.embedding_from_image(sys.argv[2])

    score = cosine_similarity(a, b)
    result = decide([("B", score)])

    print(f"Cosine similarity : {score:.4f}")
    print(f"Threshold         : {SFACE_COSINE_THRESHOLD}")
    print(f"Decision          : {'MATCH' if result['match'] else 'NO MATCH'}")
    print(f"Confidence        : {confidence_percent(score)} %")
