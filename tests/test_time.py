"""Tests for utils/time.py - age(), between(), from_datetime(), from_unix_ms()."""

import sys
import datetime
sys.path.insert(0, "src")

from pendulumium import uuid7, to_datetime, to_unix_ms
from pendulumium.utils.time import age, between, from_datetime, from_unix_ms
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

UTC = datetime.timezone.utc

# ── age() ─────────────────────────────────────────────────────────────────────

uid = str(uuid7())
a   = age(uid)

check("age: returns timedelta",              isinstance(a, datetime.timedelta))
check("age: non-negative",                   a.total_seconds() >= 0)
check("age: less than 5 seconds",            a.total_seconds() < 5)
check("age: error on invalid UUID",          raises(InvalidUUIDError, age, "not-a-uuid"))

# older ID should have a larger age
import time as _time
old_uid = str(uuid7())
_time.sleep(0.05)
new_uid = str(uuid7())
check("age: older ID has larger age",        age(old_uid) > age(new_uid))

# ── between() ─────────────────────────────────────────────────────────────────

now    = datetime.datetime.now(tz=UTC)
before = now - datetime.timedelta(seconds=10)
after  = now + datetime.timedelta(seconds=10)
uid2   = str(uuid7())

check("between: True when inside window (datetime)",   between(uid2, before, after))
check("between: False when after window (datetime)",   not between(uid2, before, before))
check("between: True when on exact boundary",          between(uid2, to_unix_ms(uid2), to_unix_ms(uid2)))

now_ms    = int(now.timestamp() * 1_000)
before_ms = now_ms - 10_000
after_ms  = now_ms + 10_000

check("between: True when inside window (int ms)",    between(uid2, before_ms, after_ms))
check("between: False when outside window (int ms)",  not between(uid2, after_ms, after_ms + 1000))
check("between: mixed datetime and int ms",           between(uid2, before, after_ms))

check("between: error on invalid UUID",               raises(InvalidUUIDError, between, "bad", before, after))
check("between: error on start > end",                raises(ValueError, between, uid2, after, before))
check("between: error on bad start type",             raises(TypeError, between, uid2, "bad", after))

# ── from_datetime() ───────────────────────────────────────────────────────────

past_dt  = datetime.datetime(2025, 1, 1, tzinfo=UTC)
past_uid = from_datetime(past_dt)

check("from_datetime: returns string",               isinstance(past_uid, str))
check("from_datetime: is valid UUID v7",             __import__('pendulumium').is_v7(past_uid))
check("from_datetime: timestamp matches input date", to_datetime(past_uid).date() == past_dt.date())
check("from_datetime: two calls differ",             from_datetime(past_dt) != from_datetime(past_dt))

check("from_datetime: error on future datetime",     raises(ValueError, from_datetime,
    datetime.datetime.now(tz=UTC) + datetime.timedelta(days=1)))
check("from_datetime: error on naive datetime",      raises(ValueError, from_datetime,
    datetime.datetime(2025, 1, 1)))
check("from_datetime: error on non-datetime",        raises(TypeError, from_datetime, 12345))
check("from_datetime: error on pre-epoch",           raises(ValueError, from_datetime,
    datetime.datetime(1960, 1, 1, tzinfo=UTC)))

# ── from_unix_ms() ────────────────────────────────────────────────────────────

past_ms  = 1_700_000_000_000
past_uid2 = from_unix_ms(past_ms)

check("from_unix_ms: returns string",               isinstance(past_uid2, str))
check("from_unix_ms: is valid UUID v7",             __import__('pendulumium').is_v7(past_uid2))
check("from_unix_ms: timestamp matches input",      to_unix_ms(past_uid2) == past_ms)
check("from_unix_ms: two calls differ",             from_unix_ms(past_ms) != from_unix_ms(past_ms))

check("from_unix_ms: error on future ms",           raises(ValueError, from_unix_ms,
    int(datetime.datetime.now(tz=UTC).timestamp() * 1_000) + 999_999))
check("from_unix_ms: error on negative",            raises(ValueError, from_unix_ms, -1))
check("from_unix_ms: error on non-int",             raises(TypeError, from_unix_ms, 1700000000.0))

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_time: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")