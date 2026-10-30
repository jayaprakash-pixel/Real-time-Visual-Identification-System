from store import Store


def seeded():
    s = Store()
    for i in range(25):
        s.add(person_id="MP001" if i % 2 else "MP002", person_name="Asha" if i % 2 else "Ravi",
              detected_at=f"2026-10-{10 + i % 5:02d}T12:{i:02d}:00", confidence=50 + i,
              camera="CAM01" if i < 15 else "PHONE1")
    return s


def test_count_and_paging():
    s = seeded()
    assert s.count() == 25
    items, total = s.list(page=1, page_size=10)
    assert total == 25 and len(items) == 10
    items3, _ = s.list(page=3, page_size=10)
    assert len(items3) == 5


def test_filters():
    s = seeded()
    assert s.list(person="MP001")[1] == 12
    assert s.list(person="ravi")[1] == 13                 # name substring, case-insensitive
    assert s.list(camera="PHONE1")[1] == 10
    assert s.list(date_from="2026-10-12", date_to="2026-10-12")[1] == 5
    assert s.list(confidence_min=70)[1] == 5
    assert s.list(confidence_max=51)[1] == 2


def test_sort_default_newest_first_and_asc():
    s = seeded()
    newest = s.list(page_size=1)[0][0]["detected_at"]
    oldest = s.list(sort_order="asc", page_size=1)[0][0]["detected_at"]
    assert newest > oldest


def test_unknown_field_rejected_and_sort_whitelist():
    s = Store()
    try:
        s.add(person_id="x", person_name="x", detected_at="t", confidence=1, camera="c", bogus=1)
        assert False, "should raise"
    except TypeError:
        pass
    s.list(sort_by="id; DROP TABLE detections")            # falls back to the default column
    assert s.count() == 0
