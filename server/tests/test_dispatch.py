from dispatch import Dispatcher


def test_failing_channel_does_not_block_others(caplog):
    got = []

    def broken(alert):
        raise RuntimeError("boom")

    d = Dispatcher()
    d.add("a", got.append)
    d.add("broken", broken)
    d.add("c", got.append)
    out = d.dispatch({"personName": "Asha"})

    assert len(got) == 2
    assert out["a"] == "ok" and out["c"] == "ok" and "boom" in out["broken"]
    assert "alert channel broken failed" in caplog.text
