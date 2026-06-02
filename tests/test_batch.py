"""Tests for core/batch.py - batch()."""

import sys
sys.path.insert(0, "src")

from pendulumium import uuid7, batch, is_v7
from pendulumium.inspection.compare import _to_int

results = []

def check(name: str, val: bool) -> None:
    results.append(("✓" if val else "✗", name))

def raises_value(fn, *args) -> bool:
    try:
        fn(*args)
        return False
    except ValueError:
        return True

# ── basic output ──────────────────────────────────────────────────────────────

ids = batch(10)

check("batch: returns list",             isinstance(ids, list))
check("batch: correct length",           len(ids) == 10)
check("batch: all strings by default",   all(isinstance(i, str) for i in ids))
check("batch: all valid UUID v7",        all(is_v7(str(i)) for i in ids))

# ── as_string / formatted flags ───────────────────────────────────────────────

ids_raw    = batch(5, formatted=False)
ids_int    = batch(5, as_string=False)

check("batch: formatted=False no hyphens",   all("-" not in str(i) for i in ids_raw))
check("batch: formatted=False length 32",    all(len(str(i)) == 32 for i in ids_raw))
check("batch: as_string=False returns ints", all(isinstance(i, int) for i in ids_int))
check("batch: as_string=False fits 128bits", all(i.bit_length() <= 128 for i in ids_int))  # type: ignore[union-attr]

# ── monotonic ordering ────────────────────────────────────────────────────────

ids_large     = batch(500)
ids_large_int = [_to_int(str(i)) for i in ids_large]

check("batch: monotonically ordered",    ids_large_int == sorted(ids_large_int))
check("batch: no duplicates",            len(set(ids_large_int)) == len(ids_large_int))

# ── interleave with uuid7() ───────────────────────────────────────────────────

# IDs from batch() must sort correctly alongside individually generated ones
before = str(uuid7())
mid    = batch(10)
after  = str(uuid7())

all_ids = [before] + [str(i) for i in mid] + [after]
all_ints = [_to_int(i) for i in all_ids]

check("batch: orders correctly with uuid7()", all_ints == sorted(all_ints))

# ── edge cases ────────────────────────────────────────────────────────────────

check("batch: n=1 works",               len(batch(1)) == 1)
check("batch: n=1 is valid UUID v7",    is_v7(str(batch(1)[0])))
check("batch: error on n=0",            raises_value(batch, 0))
check("batch: error on n=-1",           raises_value(batch, -1))

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_batch: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")