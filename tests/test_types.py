"""Tests for utils/types.py - emit_types()."""

import sys
import io
sys.path.insert(0, "src")

from pendulumium import emit_types

results = []

def check(name: str, val: bool) -> None:
    results.append(("✓" if val else "✗", name))

# ── return value ──────────────────────────────────────────────────────────────

code = emit_types(print_output=False)

check("emit_types: returns string",          isinstance(code, str))
check("emit_types: non-empty",               len(code) > 0)
check("emit_types: contains UUIDv7 type",    "UUIDv7" in code)
check("emit_types: contains branded type",   "__brand" in code)
check("emit_types: contains isUUIDv7",       "isUUIDv7" in code)
check("emit_types: contains asUUIDv7",       "asUUIDv7" in code)
check("emit_types: contains regex",          "_UUID_V7_RE" in code)
check("emit_types: contains export",         "export" in code)
check("emit_types: contains TypeError",      "TypeError" in code)
check("emit_types: is valid TypeScript-ish", "string & {" in code)

# ── print output ──────────────────────────────────────────────────────────────

captured = io.StringIO()
sys.stdout = captured
emit_types(print_output=True)
sys.stdout = sys.__stdout__
output = captured.getvalue()

check("emit_types: prints when True",        len(output) > 0)
check("emit_types: printed matches return",  output.strip() == code.strip())

# ── print_output=False silent ─────────────────────────────────────────────────

captured2 = io.StringIO()
sys.stdout = captured2
emit_types(print_output=False)
sys.stdout = sys.__stdout__

check("emit_types: silent when False",       captured2.getvalue() == "")

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_types: {passed}/{len(results)} passed\n")
for mark, name in results:
    print(f"  {mark}  {name}")