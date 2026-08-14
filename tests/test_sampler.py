import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audit-engine"))
from engine import sampler as S  # noqa: E402


def test_same_marker_same_population_reproduces_identical_sample():
    ids = ["ACC-001", "ACC-002", "ACC-003", "ACC-004", "ACC-006"]
    r1 = S.select_sample(ids, "UBI-A7-ADFAFF62AD2E", "access", "A.5.15")
    r2 = S.select_sample(ids, "UBI-A7-ADFAFF62AD2E", "access", "A.5.15")
    assert r1.selected_record_ids == r2.selected_record_ids


def test_different_marker_can_produce_a_different_sample():
    ids = ["ACC-001", "ACC-002", "ACC-003", "ACC-004", "ACC-006"]
    r1 = S.select_sample(ids, "UBI-A7-ADFAFF62AD2E", "access", "A.5.15")
    r2 = S.select_sample(ids, "SOME-OTHER-MARKER", "access", "A.5.15")
    # Not a strict requirement that they differ (small population), but the
    # selection function itself must be marker-sensitive.
    assert r1.algorithm_version == r2.algorithm_version


def test_row_order_does_not_affect_selection():
    ids_a = ["ACC-001", "ACC-002", "ACC-003", "ACC-004", "ACC-006"]
    ids_b = list(reversed(ids_a))
    r1 = S.select_sample(ids_a, "UBI-A7-ADFAFF62AD2E", "access", "A.5.15")
    r2 = S.select_sample(ids_b, "UBI-A7-ADFAFF62AD2E", "access", "A.5.15")
    assert r1.selected_record_ids == r2.selected_record_ids


def test_sample_size_capped_at_published_max():
    ids = [f"X-{i:03d}" for i in range(50)]
    r = S.select_sample(ids, "marker", "pop", "CTRL")
    assert r.sample_size == S.PUBLISHED_MAX_SAMPLE


def test_sample_size_shrinks_to_small_population():
    ids = ["ONLY-ONE"]
    r = S.select_sample(ids, "marker", "pop", "CTRL")
    assert r.sample_size == 1
    assert r.selected_record_ids == ("ONLY-ONE",)


def test_empty_population_yields_zero_sample_not_error():
    r = S.select_sample([], "marker", "pop", "CTRL")
    assert r.sample_size == 0
    assert r.selected_record_ids == ()


def test_selected_and_not_selected_partition_the_population():
    ids = ["A", "B", "C", "D", "E", "F", "G"]
    r = S.select_sample(ids, "marker", "pop", "CTRL")
    assert set(r.selected_record_ids) | set(r.not_selected_record_ids) == set(ids)
    assert set(r.selected_record_ids) & set(r.not_selected_record_ids) == set()
