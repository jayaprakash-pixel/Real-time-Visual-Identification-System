from gate import MatchGate


def result(**over):
    r = dict(person_id="MP001", name="Asha", confidence_percent=80.0, camera_id="CAM01",
             timestamp="2026-10-30T12:00:00", scene_image="x.jpg")
    r.update(over)
    return r


def test_accepts_strong_result():
    assert MatchGate().check(result()) == (True, "ok")


def test_rejects_below_threshold():
    ok, why = MatchGate(min_percent=55).check(result(confidence_percent=54.9))
    assert not ok and "below threshold" in why


def test_cooldown_then_accept_after():
    t = [0.0]
    g = MatchGate(cooldown=30, clock=lambda: t[0])
    assert g.check(result())[0]
    t[0] = 10
    ok, why = g.check(result())
    assert not ok and "cooldown" in why
    assert g.check(result(person_id="MP002"))[0]           # other person is independent
    t[0] = 31
    assert g.check(result())[0]


def test_rejected_result_does_not_start_cooldown():
    g = MatchGate()
    assert not g.check(result(confidence_percent=10))[0]
    assert g.check(result())[0]


def test_malformed():
    ok, why = MatchGate().check(result(scene_image=None))
    assert not ok and "scene_image" in why
    ok, why = MatchGate().check(result(confidence_percent="high"))
    assert not ok and "not a number" in why
