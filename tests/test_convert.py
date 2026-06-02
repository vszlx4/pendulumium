"""Tests for _convert.py - to_hex(), to_int(), to_bytes(), from_int(), from_bytes()."""

import sys
sys.path.insert(0, "src")

from pendulumium import uuid7, to_hex, to_int, to_bytes, from_int, from_bytes
from pendulumium.exceptions import InvalidUUIDError

results = []

def check(name: str, val: bool) -> None:
    results.append(("✓" if val else "✗", name))

def raises_invalid(fn, *args) -> bool:
    try:
        fn(*args)
        return False
    except InvalidUUIDError:
        return True

def raises_value(fn, *args) -> bool:
    try:
        fn(*args)
        return False
    except ValueError:
        return True

uid = str(uuid7())

# ── to_hex() ──────────────────────────────────────────────────────────────────

h = to_hex(uid)

check("to_hex: returns str",              isinstance(h, str))
check("to_hex: length is 32",            len(h) == 32)
check("to_hex: no hyphens",              "-" not in h)
check("to_hex: all hex characters",      all(c in "0123456789abcdefABCDEF" for c in h))
check("to_hex: error on invalid",        raises_invalid(to_hex, "not-a-uuid"))

# ── to_int() ──────────────────────────────────────────────────────────────────

i = to_int(uid)

check("to_int: returns int",             isinstance(i, int))
check("to_int: fits 128 bits",           i.bit_length() <= 128)
check("to_int: positive",                i > 0)
check("to_int: error on invalid",        raises_invalid(to_int, "not-a-uuid"))

# ── to_bytes() ────────────────────────────────────────────────────────────────

b = to_bytes(uid)

check("to_bytes: returns bytes",         isinstance(b, bytes))
check("to_bytes: length is 16",          len(b) == 16)
check("to_bytes: error on invalid",      raises_invalid(to_bytes, "not-a-uuid"))

# ── from_int() ────────────────────────────────────────────────────────────────

check("from_int: roundtrip",             from_int(to_int(uid)) == uid)
check("from_int: formatted default",     from_int(to_int(uid)).count("-") == 4)
check("from_int: unformatted",           "-" not in from_int(to_int(uid), formatted=False))
check("from_int: unformatted length 32", len(from_int(to_int(uid), formatted=False)) == 32)
check("from_int: error on negative",     raises_value(from_int, -1))
check("from_int: error on overflow",     raises_value(from_int, (1 << 128)))

# ── from_bytes() ──────────────────────────────────────────────────────────────

check("from_bytes: roundtrip",           from_bytes(to_bytes(uid)) == uid)
check("from_bytes: formatted default",   from_bytes(to_bytes(uid)).count("-") == 4)
check("from_bytes: unformatted",         "-" not in from_bytes(to_bytes(uid), formatted=False))
check("from_bytes: error on 15 bytes",   raises_value(from_bytes, b"\x00" * 15))
check("from_bytes: error on 17 bytes",   raises_value(from_bytes, b"\x00" * 17))
check("from_bytes: error on empty",      raises_value(from_bytes, b""))

# ── cross-function consistency ─────────────────────────────────────────────────

check("consistency: hex -> int matches to_int",       int(to_hex(uid), 16) == to_int(uid))
check("consistency: bytes -> int matches to_int",     int.from_bytes(to_bytes(uid), 'big') == to_int(uid))
check("consistency: from_int(from_bytes) roundtrip",  from_bytes(to_bytes(uid)) == from_int(to_int(uid)))

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_convert: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")