"""Tests for _decoder.py — decode(), to_datetime(), to_unix_ms()."""

import sys
import time
import datetime

sys.path.insert(0, "src")

from typing import cast

from pendulumium import uuid7, decode, to_datetime, to_unix_ms
from pendulumium.exceptions import InvalidUUIDError

results = []

def check(name: str, val: bool) -> None:
    results.append(("✓" if val else "✗", name))

def raises(fn, *args) -> bool:
    try:
        fn(*args)
        return False
    except InvalidUUIDError:
        return True

# ── decode() ──────────────────────────────────────────────────────────────────

# before
uid  = str(uuid7())
info = decode(uid)

check("decode: returns dict",            isinstance(info, dict))
check("decode: version is 7",            info["version"] == 7)
check("decode: variant string correct",  info["variant"] == "0b10 (RFC 9562)")
check("decode: datetime is aware UTC",   (
    isinstance(info["datetime_utc"], datetime.datetime)
    and cast(datetime.datetime, info["datetime_utc"]).tzinfo == datetime.timezone.utc
))
check("decode: uuid_int is int",         isinstance(info["uuid_int"], int))
check("decode: uuid_int fits 128 bits",  cast(int, info["uuid_int"]).bit_length() <= 128)
check("decode: normalized lowercase",    cast(str, info["uuid"]) == cast(str, info["uuid"]).lower())
check("decode: normalized has hyphens",  cast(str, info["uuid"]).count("-") == 4)
check("decode: sequence in range",       0 <= cast(int, info["sequence"]) <= 0x3FFF)
check("decode: sub_ms in range",         0 <= cast(int, info["sub_ms"]) <= 0xFFF)
check("decode: sub_ms_ns in range",      0 <= cast(int, info["sub_ms_ns"]) <= 999_999)
check("decode: node_id in range",        0 <= cast(int, info["node_id"]) <= 0xFFFF)
check("decode: entropy in range",        0 <= cast(int, info["entropy"]) <= 0xFFFF_FFFF)

before_ms = int(time.time() * 1000)
uid2      = str(uuid7())
after_ms  = int(time.time() * 1000)
ts_ms     = cast(int, decode(uid2)["timestamp_ms"])

check("decode: timestamp_ms within capture window", before_ms <= ts_ms <= after_ms)
check("decode: timestamp_ns >= timestamp_ms * 1e6", cast(int, info["timestamp_ns"]) >= cast(int, info["timestamp_ms"]) * 1_000_000)

# ── case insensitivity ────────────────────────────────────────────────────────

info_upper = decode(uid.upper())
check("decode: case-insensitive input",  info_upper["uuid"] == info["uuid"])

# ── to_datetime() ─────────────────────────────────────────────────────────────

dt = to_datetime(uid)
check("to_datetime: returns datetime",   isinstance(dt, datetime.datetime))
check("to_datetime: is UTC-aware",       dt.tzinfo == datetime.timezone.utc)
check("to_datetime: matches decode",     dt == info["datetime_utc"])

# ── to_unix_ms() ──────────────────────────────────────────────────────────────

ms = to_unix_ms(uid)
check("to_unix_ms: returns int",         isinstance(ms, int))
check("to_unix_ms: matches decode",      ms == info["timestamp_ms"])
check("to_unix_ms: plausible value",     ms > 1_700_000_000_000)

# ── error cases ───────────────────────────────────────────────────────────────

check("error: plain string",           raises(decode, "not-a-uuid"))
check("error: empty string",           raises(decode, ""))
check("error: wrong version (v4)",     raises(decode, "550e8400-e29b-41d4-a716-446655440000"))
check("error: too short",              raises(decode, "019e2c01-6909-7583-800a"))

try:
    decode("bad-input-xyz")
except InvalidUUIDError as e:
    check("error: .value attribute set", e.value == "bad-input-xyz")

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_decoder: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")