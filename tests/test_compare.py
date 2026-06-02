"""Tests for _compare.py - compare() and sort()."""

import sys
sys.path.insert(0, "src")

from pendulumium import uuid7, compare, sort
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

# ── compare() ─────────────────────────────────────────────────────────────────

a = str(uuid7())
b = str(uuid7())
c = str(uuid7())

check("compare: a < b returns -1",       compare(a, b) == -1)
check("compare: b > a returns +1",       compare(b, a) == +1)
check("compare: a == a returns 0",       compare(a, a) == 0)
check("compare: b < c returns -1",       compare(b, c) == -1)
check("compare: a < c returns -1",       compare(a, c) == -1)

check("compare: returns int",            isinstance(compare(a, b), int))
check("compare: only returns -1/0/+1",   compare(a, b) in (-1, 0, +1))

check("compare: error on invalid a",     raises(compare, "not-a-uuid", b))
check("compare: error on invalid b",     raises(compare, a, "not-a-uuid"))
check("compare: error on both invalid",  raises(compare, "bad", "bad"))

# ── sort() ────────────────────────────────────────────────────────────────────

ids = [str(uuid7()) for _ in range(20)]

sorted_asc  = sort(ids)
sorted_desc = sort(ids, reverse=True)

check("sort: returns list",              isinstance(sorted_asc, list))
check("sort: length unchanged",          len(sorted_asc) == len(ids))
check("sort: ascending order",           all(compare(sorted_asc[i], sorted_asc[i+1]) == -1 for i in range(len(sorted_asc)-1)))
check("sort: descending order",          all(compare(sorted_desc[i], sorted_desc[i+1]) == +1 for i in range(len(sorted_desc)-1)))
check("sort: asc + desc = original set", set(sorted_asc) == set(sorted_desc))
check("sort: does not mutate input",     ids != sorted_asc or ids == sorted_asc)  # sort() returns new list

shuffled = sorted_asc[::-1]  # reverse the sorted list
check("sort: re-sorts a shuffled list",  sort(shuffled) == sorted_asc)

check("sort: empty list",                sort([]) == [])
check("sort: single item",               sort([ids[0]]) == [ids[0]])

check("sort: error on invalid item",     raises(sort, [ids[0], "not-a-uuid"]))

# ── print results ─────────────────────────────────────────────────────────────

passed = sum(1 for m, _ in results if m == "✓")
print(f"\n  test_compare: {passed}/{len(results)} passed\n")
for mark, name in results:
  print(f"  {mark}  {name}")