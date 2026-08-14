"""Deterministic, marker-seeded sampler.

Sample size rule (documented engine policy, see decision log D-003; the
brief and populations pack do not hand down an explicit sample-size table,
so this rule is published here and enforced identically on every run):

    sample_size = min(PUBLISHED_MAX_SAMPLE, eligible_count)   if eligible_count > 0
    sample_size = 0                                            if eligible_count == 0

PUBLISHED_MAX_SAMPLE = 3.

Selection is order-independent: eligible record_ids are sorted lexically
before seeding so that re-running against the same CSV in a different row
order still produces the same sample.
"""
from __future__ import annotations
import hashlib
import random
from dataclasses import dataclass

PUBLISHED_MAX_SAMPLE = 3
ALGORITHM_VERSION = "marker-seeded-sha256-v1"


def _seed_from(marker: str, population: str, control_id: str) -> int:
    digest = hashlib.sha256(f"{marker}|{population}|{control_id}".encode("utf-8")).hexdigest()
    return int(digest[:16], 16)


@dataclass(frozen=True)
class SampleResult:
    population: str
    control_id: str
    marker: str
    algorithm_version: str
    eligible_count: int
    sample_size: int
    selected_record_ids: tuple
    not_selected_record_ids: tuple


def select_sample(eligible_record_ids: list, marker: str, population: str,
                   control_id: str) -> SampleResult:
    ordered = sorted(set(eligible_record_ids))
    eligible_count = len(ordered)
    sample_size = min(PUBLISHED_MAX_SAMPLE, eligible_count)
    rng = random.Random(_seed_from(marker, population, control_id))
    shuffled = ordered[:]
    rng.shuffle(shuffled)
    selected = tuple(sorted(shuffled[:sample_size]))
    not_selected = tuple(sorted(set(ordered) - set(selected)))
    return SampleResult(
        population=population,
        control_id=control_id,
        marker=marker,
        algorithm_version=ALGORITHM_VERSION,
        eligible_count=eligible_count,
        sample_size=sample_size,
        selected_record_ids=selected,
        not_selected_record_ids=not_selected,
    )
