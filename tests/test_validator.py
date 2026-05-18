"""Tests for _validator.py — is_valid() and is_v7()."""

import sys
sys.path.insert(0, "src")

from pendulumium import uuid7, is_valid, is_v7

results = []

def check(name: str, val: bool) -> None:
  results.append(("✓" if val else "✗", name))

# ── is_valid() ────────────────────────────────────────────────────────────────

uid = str(uuid7())

check("is_valid: accepts generated UUID",        is_valid(uid))
check("is_valid: accepts uppercase",             is_valid(uid.upper()))
check("is_valid: accepts mixed case",            is_valid(uid.swapcase()))
check("is_valid: rejects plain string",          not is_valid("not-a-uuid"))
check("is_valid: rejects empty string",          not is_valid(""))
check("is_valid: rejects missing hyphens",       not is_valid(uid.replace("-", "")))
check("is_valid: rejects too short",             not is_valid("019e2c01-6909-7583-800a"))
check("is_valid: rejects too long",              not is_valid(uid + "00"))
check("is_valid: rejects invalid hex char",      not is_valid("019e2c01-6909-7583-800a-8afe6057zzzz"))
check("is_valid: accepts v4 UUID",               is_valid("550e8400-e29b-41d4-a716-446655440000"))
check("is_valid: accepts all zeros",             is_valid("00000000-0000-0000-0000-000000000000"))

# ── is_v7() ───────────────────────────────────────────────────────────────────

check("is_v7: accepts generated UUID",           is_v7(uid))
check("is_v7: accepts uppercase",                is_v7(uid.upper()))
check("is_v7: rejects plain string",             not is_v7("not-a-uuid"))
check("is_v7: rejects empty string",             not is_v7(""))
check("is_v7: rejects v4 UUID",                  not is_v7("550e8400-e29b-41d4-a716-446655440000"))
check("is_v7: rejects v1 UUID",                  not is_v7("6ba7b810-9dad-11d1-80b4-00c04fd430c8"))
check("is_v7: rejects all zeros",                not is_v7("00000000-0000-0000-0000-000000000000"))
check("is_v7: rejects wrong variant",            not is_v7("019e2c01-6909-7000-c00a-8afe60572a94"))

# ── consistency between is_valid and is_v7 ───────────────────────────────────

# anything is_v7 approves must also pass is_valid
check("consistency: is_v7 implies is_valid",     is_valid(uid) if is_v7(uid) else True)

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_validator: {passed}/{len(results)} passed\n")
for mark, name in results:
  print(f"  {mark}  {name}")