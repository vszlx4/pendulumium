"""Tests for inspection/gaps.py - find_gaps()."""

import sys
import datetime
sys.path.insert(0, "src")

from typing import cast
from pendulumium import uuid7, batch, find_gaps
from pendulumium.utils.time import between_times
from pendulumium.core.exceptions import InvalidUUIDError

results = []

def check(name: str, val: bool) -> None:
    results.append(("✓" if val else "✗", name))

def raises(exc, fn, *args, **kwargs) -> bool:
    try:
        fn(*args, **kwargs)
        return False
    except exc:
        return True

UTC = datetime.timezone.utc

# ── no gaps ───────────────────────────────────────────────────────────────────

ids    = batch(100)
result = find_gaps(ids, threshold_ms=60_000)  # type: ignore[arg-type]

check("find_gaps: returns dict",           isinstance(result, dict))
check("find_gaps: has total key",          "total" in result)
check("find_gaps: has gaps key",           "gaps" in result)
check("find_gaps: has details key",        "details" in result)
check("find_gaps: total correct",          cast(int, result["total"]) == 100)
check("find_gaps: no gaps in batch",       cast(int, result["gaps"]) == 0)
check("find_gaps: details empty",          cast(list, result["details"]) == [])

# ── with injected gaps ────────────────────────────────────────────────────────

# use between_times to create IDs spread across a known time range
# so we can guarantee gaps exist between clusters
start1 = datetime.datetime(2025, 1,  1, tzinfo=UTC)
end1   = datetime.datetime(2025, 1,  2, tzinfo=UTC)
start2 = datetime.datetime(2025, 6,  1, tzinfo=UTC)
end2   = datetime.datetime(2025, 6,  2, tzinfo=UTC)

cluster_a = between_times(start1, end1, n=5)
cluster_b = between_times(start2, end2, n=5)
gapped    = cluster_a + cluster_b

result2 = find_gaps(gapped, threshold_ms=1_000)

check("find_gaps: detects gap between clusters",  cast(int, result2["gaps"]) >= 1)

details = cast(list, result2["details"])
check("find_gaps: details is list",               isinstance(details, list))

if details:
    first = details[0]
    check("find_gaps: detail has before",         "before" in first)    # type: ignore[operator]
    check("find_gaps: detail has after",          "after" in first)     # type: ignore[operator]
    check("find_gaps: detail has gap_ms",         "gap_ms" in first)    # type: ignore[operator]
    check("find_gaps: detail has gap_seconds",    "gap_seconds" in first) # type: ignore[operator]
    check("find_gaps: detail has index",          "index" in first)     # type: ignore[operator]
    check("find_gaps: gap_ms is positive",        cast(int, first["gap_ms"]) > 0)   # type: ignore[index]
    check("find_gaps: gap_seconds matches ms",    cast(float, first["gap_seconds"]) == round(cast(int, first["gap_ms"]) / 1_000, 3))  # type: ignore[index]

# ── threshold filtering ───────────────────────────────────────────────────────

# high threshold — nothing reported (gap between clusters is ~150 days = ~13 billion ms)
result3 = find_gaps(gapped, threshold_ms=14_000_000_000)
check("find_gaps: high threshold finds nothing", cast(int, result3["gaps"]) == 0)

# threshold of 1ms — catches everything with any gap
result4 = find_gaps(gapped, threshold_ms=1)
check("find_gaps: low threshold finds gaps",     cast(int, result4["gaps"]) >= 1)

# ── edge cases ────────────────────────────────────────────────────────────────

check("find_gaps: error on single item",         raises(ValueError, find_gaps, [str(uuid7())]))
check("find_gaps: error on empty list",          raises(ValueError, find_gaps, []))
check("find_gaps: error on threshold < 1",       raises(ValueError, find_gaps, [str(uuid7()), str(uuid7())], 0))
check("find_gaps: error on invalid UUID",        raises(InvalidUUIDError, find_gaps, [str(uuid7()), "not-a-uuid"]))
check("find_gaps: two items no gap",             cast(int, find_gaps([str(uuid7()), str(uuid7())], threshold_ms=60_000)["gaps"]) == 0)

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_gaps: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")