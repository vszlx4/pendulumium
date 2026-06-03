"""Tests for inspection/collisions.py - check_collisions()."""

import sys
sys.path.insert(0, "src")

from typing import cast
from pendulumium import uuid7, batch, check_collisions
from pendulumium.core.exceptions import InvalidUUIDError

results = []

def check(name: str, val: bool) -> None:
    results.append(("✓" if val else "✗", name))

def raises(exc, fn, *args) -> bool:
    try:
        fn(*args)
        return False
    except exc:
        return True

# ── clean list — no collisions ────────────────────────────────────────────────

ids    = batch(1_000)
result = check_collisions(ids)  # type: ignore[arg-type]

check("collisions: returns dict",              isinstance(result, dict))
check("collisions: has total key",             "total" in result)
check("collisions: has collisions key",        "collisions" in result)
check("collisions: has duplicates key",        "duplicates" in result)
check("collisions: total correct",             cast(int, result["total"]) == 1_000)
check("collisions: zero collisions",           cast(int, result["collisions"]) == 0)
check("collisions: duplicates list empty",     cast(list, result["duplicates"]) == [])

# ── list with injected duplicates ─────────────────────────────────────────────

uid_a   = str(uuid7())
uid_b   = str(uuid7())
uid_c   = str(uuid7())
dirty   = [uid_a, uid_b, uid_a, uid_c, uid_b, uid_a]
result2 = check_collisions(dirty)

check("collisions: detects duplicates",        cast(int, result2["collisions"]) == 2)
check("collisions: total correct",             cast(int, result2["total"]) == 6)

dupes = cast(list, result2["duplicates"])
uuids_found = [d["uuid"] for d in dupes]  # type: ignore[index]
check("collisions: reports uid_a",             uid_a.lower() in uuids_found)
check("collisions: reports uid_b",             uid_b.lower() in uuids_found)

positions_a = next(d["positions"] for d in dupes if d["uuid"] == uid_a.lower())  # type: ignore[index]
check("collisions: uid_a positions correct",   positions_a == [0, 2, 5])

positions_b = next(d["positions"] for d in dupes if d["uuid"] == uid_b.lower())  # type: ignore[index]
check("collisions: uid_b positions correct",   positions_b == [1, 4])

# ── case insensitivity ────────────────────────────────────────────────────────

uid_upper = str(uuid7())
mixed     = [uid_upper, uid_upper.lower()]
result3   = check_collisions(mixed)
check("collisions: case-insensitive detection", cast(int, result3["collisions"]) == 1)

# ── edge cases ────────────────────────────────────────────────────────────────

check("collisions: single item no collision",  cast(int, check_collisions([str(uuid7())])["collisions"]) == 0)
check("collisions: error on empty list",       raises(ValueError, check_collisions, []))
check("collisions: error on invalid UUID",     raises(InvalidUUIDError, check_collisions, [str(uuid7()), "not-a-uuid"]))

# ── large batch — stress test ─────────────────────────────────────────────────

large  = batch(10_000)
result4 = check_collisions(large)  # type: ignore[arg-type]
check("collisions: 10k batch zero collisions", cast(int, result4["collisions"]) == 0)

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_collisions: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")