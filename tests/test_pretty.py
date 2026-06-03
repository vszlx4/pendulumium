"""Tests for inspection/pretty.py - pretty()."""

import sys
import io
sys.path.insert(0, "src")

from pendulumium import uuid7, pretty
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

uid = str(uuid7())

# ── return value ──────────────────────────────────────────────────────────────

info = pretty(uid, print_output=False)

check("pretty: returns dict",            isinstance(info, dict))
check("pretty: has timestamp_ms",        "timestamp_ms" in info)
check("pretty: has datetime_utc",        "datetime_utc" in info)
check("pretty: has version",             "version" in info)
check("pretty: has variant",             "variant" in info)
check("pretty: has sequence",            "sequence" in info)
check("pretty: has node_id",             "node_id" in info)
check("pretty: has entropy",             "entropy" in info)
check("pretty: version is 7",            info["version"] == 7)

# ── print output ──────────────────────────────────────────────────────────────

captured = io.StringIO()
sys.stdout = captured
pretty(uid, print_output=True)
sys.stdout = sys.__stdout__
output = captured.getvalue()

check("pretty: prints the UUID",         uid in output)
check("pretty: prints timestamp label",  "timestamp" in output)
check("pretty: prints sub-ms label",     "sub-ms" in output)
check("pretty: prints version label",    "version" in output)
check("pretty: prints variant label",    "variant" in output)
check("pretty: prints sequence label",   "sequence" in output)
check("pretty: prints node ID label",    "node ID" in output)
check("pretty: prints entropy label",    "entropy" in output)
check("pretty: prints UTC",              "UTC" in output)

# ── print_output=False produces no output ─────────────────────────────────────

captured2 = io.StringIO()
sys.stdout = captured2
pretty(uid, print_output=False)
sys.stdout = sys.__stdout__

check("pretty: print_output=False silent", captured2.getvalue() == "")

# ── error handling ────────────────────────────────────────────────────────────

check("pretty: error on invalid UUID",   raises(InvalidUUIDError, pretty, "not-a-uuid"))

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_pretty: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")