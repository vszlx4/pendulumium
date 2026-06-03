"""Tests for core/stream.py - stream()."""

import sys
sys.path.insert(0, "src")

from typing import Iterator
from pendulumium import uuid7, stream, is_v7
from pendulumium.inspection.compare import _to_int

results = []

def check(name: str, val: bool) -> None:
    results.append(("✓" if val else "✗", name))

def raises_value(fn, *args, **kwargs) -> bool:
    try:
        fn(*args, **kwargs)
        return False
    except ValueError:
        return True

# ── return type ───────────────────────────────────────────────────────────────

s = stream(5)
check("stream: returns iterator",         hasattr(s, "__iter__") and hasattr(s, "__next__"))
check("stream: is Iterator",              isinstance(s, Iterator))

# ── finite stream ─────────────────────────────────────────────────────────────

ids = [str(i) for i in stream(10)]
check("stream: finite length correct",    len(ids) == 10)
check("stream: all strings by default",   all(isinstance(i, str) for i in ids))
check("stream: all valid UUID v7",        all(is_v7(i) for i in ids))

ids_raw = [str(i) for i in stream(5, formatted=False)]
check("stream: formatted=False no hyphens", all("-" not in i for i in ids_raw))
check("stream: formatted=False length 32",  all(len(i) == 32 for i in ids_raw))

ids_int = list(stream(5, as_string=False))
check("stream: as_string=False ints",     all(isinstance(i, int) for i in ids_int))
check("stream: as_string=False 128-bit",  all(i.bit_length() <= 128 for i in ids_int))  # type: ignore[union-attr]

# ── monotonic ordering ────────────────────────────────────────────────────────

ids_large     = [str(i) for i in stream(500)]
ids_large_int = [_to_int(i) for i in ids_large]
check("stream: monotonically ordered",    ids_large_int == sorted(ids_large_int))
check("stream: no duplicates",            len(set(ids_large_int)) == len(ids_large_int))

# ── infinite stream ───────────────────────────────────────────────────────────

collected = []
for uid in stream():
    collected.append(uid)
    if len(collected) == 100:
        break

check("stream: infinite yields correctly", len(collected) == 100)
check("stream: infinite all valid UUID v7", all(is_v7(i) for i in collected))

# ── interleave with uuid7() ───────────────────────────────────────────────────

before   = str(uuid7())
streamed = [str(i) for i in stream(10)]
after    = str(uuid7())

all_ids: list[str] = [before] + streamed + [after]
all_ints = [_to_int(i) for i in all_ids]
check("stream: orders correctly with uuid7()", all_ints == sorted(all_ints))

# ── edge cases ────────────────────────────────────────────────────────────────

check("stream: n=1 yields one ID",        len(list(stream(1))) == 1)
check("stream: error on n=0",             raises_value(list, stream(0)))
check("stream: error on n=-1",            raises_value(list, stream(-1)))

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_stream: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")