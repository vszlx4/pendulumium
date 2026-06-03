"""Tests for utils/sql.py - sql_range()."""

import sys
import datetime
sys.path.insert(0, "src")

from pendulumium import uuid7, is_v7, sql_range
from pendulumium.inspection.compare import _to_int
from pendulumium.utils.time import from_datetime

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

start_dt = datetime.datetime(2025, 1,  1, tzinfo=UTC)
end_dt   = datetime.datetime(2025, 12, 31, tzinfo=UTC)

lower, upper = sql_range(start_dt, end_dt)

# ── return type ───────────────────────────────────────────────────────────────

check("sql_range: returns tuple",            isinstance((lower, upper), tuple))
check("sql_range: lower is string",          isinstance(lower, str))
check("sql_range: upper is string",          isinstance(upper, str))
check("sql_range: lower is valid UUID v7",   is_v7(lower))
check("sql_range: upper is valid UUID v7",   is_v7(upper))

# ── ordering ──────────────────────────────────────────────────────────────────

check("sql_range: lower < upper",            _to_int(lower) < _to_int(upper))

# ── IDs inside range fall between boundaries ──────────────────────────────────

mid_dt  = datetime.datetime(2025, 6, 15, tzinfo=UTC)
mid_uid = from_datetime(mid_dt)

check("sql_range: mid-range ID > lower",     _to_int(mid_uid) > _to_int(lower))
check("sql_range: mid-range ID < upper",     _to_int(mid_uid) < _to_int(upper))

# ── IDs outside range fall outside boundaries ─────────────────────────────────

before_dt  = datetime.datetime(2024, 1, 1, tzinfo=UTC)
after_dt   = datetime.datetime(2026, 1, 1, tzinfo=UTC)
before_uid = from_datetime(before_dt)
after_uid  = from_datetime(after_dt)

check("sql_range: before-range ID < lower",  _to_int(before_uid) < _to_int(lower))
check("sql_range: after-range ID > upper",   _to_int(after_uid)  > _to_int(upper))

# ── accepts int ms ────────────────────────────────────────────────────────────

start_ms = int(start_dt.timestamp() * 1_000)
end_ms   = int(end_dt.timestamp()   * 1_000)
lower2, upper2 = sql_range(start_ms, end_ms)

check("sql_range: accepts int ms",           is_v7(lower2) and is_v7(upper2))
check("sql_range: int ms matches datetime",  lower == lower2)

# ── mixed types ───────────────────────────────────────────────────────────────

lower3, upper3 = sql_range(start_dt, end_ms)
check("sql_range: mixed datetime and int",   is_v7(lower3) and is_v7(upper3))

# ── error cases ───────────────────────────────────────────────────────────────

check("sql_range: error on start >= end",    raises(ValueError, sql_range, end_dt, start_dt))
check("sql_range: error on start == end",    raises(ValueError, sql_range, start_ms, start_ms))
check("sql_range: error on negative start",  raises(ValueError, sql_range, -1, end_ms))
check("sql_range: error on bad type",        raises(TypeError,  sql_range, "bad", end_dt))

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_sql: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")