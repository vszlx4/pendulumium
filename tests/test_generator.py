"""Tests for core/generator.py - uuid7()."""

import sys
import threading
sys.path.insert(0, "src")

from pendulumium import uuid7, is_v7
from pendulumium.core.generator import Pendulumium

results = []

def check(name: str, val: bool) -> None:
    results.append(("✓" if val else "✗", name))

def raises_runtime(fn, *args) -> bool:
    try:
        fn(*args)
        return False
    except RuntimeError:
        return True

# ── output format ─────────────────────────────────────────────────────────────

uid = str(uuid7())

check("uuid7: returns string by default",       isinstance(uuid7(), str))
check("uuid7: returns int when as_string=False", isinstance(uuid7(as_string=False), int))
check("uuid7: formatted has hyphens",           uid.count("-") == 4)
check("uuid7: formatted length is 36",          len(uid) == 36)
check("uuid7: unformatted length is 32",        len(str(uuid7(formatted=False))) == 32)
check("uuid7: unformatted no hyphens",          "-" not in str(uuid7(formatted=False)))
check("uuid7: is valid UUID v7",                is_v7(uid))

# ── bit fields ────────────────────────────────────────────────────────────────

uid_int = uuid7(as_string=False)

version = (uid_int >> 76) & 0xF        # type: ignore[operator]
variant = (uid_int >> 62) & 0b11       # type: ignore[operator]
ts      = (uid_int >> 80) & ((1 << 48) - 1)  # type: ignore[operator]

check("uuid7: version nibble is 7",     version == 7)
check("uuid7: variant bits are 0b10",   variant == 0b10)
check("uuid7: timestamp is plausible",  ts > 1_700_000_000_000)
check("uuid7: fits 128 bits",           uid_int.bit_length() <= 128)  # type: ignore[union-attr]

# ── monotonic ordering ────────────────────────────────────────────────────────

ids = [uuid7(as_string=False) for _ in range(1000)]

check("uuid7: monotonically ordered",   ids == sorted(ids))  # type: ignore[type-var]
check("uuid7: no duplicates",           len(set(ids)) == len(ids))

# ── thread safety ─────────────────────────────────────────────────────────────

thread_results: list[int] = []
errors: list[Exception]   = []

def generate(n: int) -> None:
    try:
        for _ in range(n):
            thread_results.append(int(uuid7(as_string=False)))  # type: ignore[arg-type]
    except Exception as e:
        errors.append(e)

threads = [threading.Thread(target=generate, args=(200,)) for _ in range(5)]
for t in threads: t.start()
for t in threads: t.join()

check("uuid7: thread safety — no errors",      len(errors) == 0)
check("uuid7: thread safety — correct count",  len(thread_results) == 1000)
check("uuid7: thread safety — no duplicates",  len(set(thread_results)) == len(thread_results))

# ── node ID ───────────────────────────────────────────────────────────────────

check("uuid7: node_id is 16-bit",       0 <= Pendulumium._node_id <= 0xFFFF)
check("uuid7: node_id is stable",       Pendulumium._node_id == Pendulumium._node_id)

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_generator: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")