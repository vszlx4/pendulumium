"""Tests for bench/runner.py - run() and profile()."""

import sys
sys.path.insert(0, "src")

from typing import cast
from pendulumium.bench import run, profile

results = []

def check(name: str, val: bool) -> None:
    results.append(("✓" if val else "✗", name))

def raises(exc, fn, *args, **kwargs) -> bool:
    try:
        fn(*args, **kwargs)
        return False
    except exc:
        return True

# ── run() ─────────────────────────────────────────────────────────────────────

result = run(1_000, verbose=False)

check("run: returns dict",                isinstance(result, dict))
check("run: has n",                       "n" in result)
check("run: has gen_time_ms",             "gen_time_ms" in result)
check("run: has gen_per_second",          "gen_per_second" in result)
check("run: has batch_time_ms",           "batch_time_ms" in result)
check("run: has batch_per_second",        "batch_per_second" in result)
check("run: has decode_time_ms",          "decode_time_ms" in result)
check("run: has decode_per_second",       "decode_per_second" in result)
check("run: has collisions",              "collisions" in result)

check("run: n correct",                   cast(int, result["n"]) == 1_000)
check("run: gen_time_ms positive",        cast(float, result["gen_time_ms"]) > 0)
check("run: gen_per_second positive",     cast(int, result["gen_per_second"]) > 0)
check("run: batch_per_second positive",   cast(int, result["batch_per_second"]) > 0)
check("run: decode_per_second positive",  cast(int, result["decode_per_second"]) > 0)
check("run: zero collisions",             cast(int, result["collisions"]) == 0)

check("run: error on n=0",                raises(ValueError, run, 0, verbose=False))
check("run: error on n=-1",               raises(ValueError, run, -1, verbose=False))

# ── profile() ─────────────────────────────────────────────────────────────────

prof = profile(0.5, verbose=False)

check("profile: returns dict",            isinstance(prof, dict))
check("profile: has duration_s",          "duration_s" in prof)
check("profile: has total_generated",     "total_generated" in prof)
check("profile: has avg_per_second",      "avg_per_second" in prof)
check("profile: has peak_per_ms",         "peak_per_ms" in prof)
check("profile: has overflows",           "overflows" in prof)

check("profile: duration close to 0.5s",  0.4 <= cast(float, prof["duration_s"]) <= 1.0)
check("profile: total_generated > 0",     cast(int, prof["total_generated"]) > 0)
check("profile: avg_per_second > 0",      cast(int, prof["avg_per_second"]) > 0)
check("profile: overflows non-negative",  cast(int, prof["overflows"]) >= 0)

check("profile: error on seconds < 0.1",  raises(ValueError, profile, 0.05, verbose=False))

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_bench: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")