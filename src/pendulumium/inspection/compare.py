"""
compare.py - chronological comparison and sorting for UUID v7 strings.

UUID v7 is designed so that lexicographic order equals chronological order
— the timestamp occupies the most significant bits, so integer comparison
of the 128-bit value is sufficient. No field extraction needed.
"""

from __future__ import annotations

from ..core.exceptions import InvalidUUIDError
from .validator import is_v7


def _to_int(uuid: str) -> int:
  """Parse a validated UUID v7 string into a 128-bit integer."""
  if not is_v7(uuid):
    raise InvalidUUIDError(uuid)
  return int(uuid.replace("-", ""), 16)

def compare(a: str, b: str) -> int:
  """
  Compare two UUID v7 strings chronologically.

  Returns:
    -1 if a was created before b
     0 if a and b are identical
    +1 if a was created after b

  Raises:
    InvalidUUIDError - if either string is not a valid UUID v7.

  Example:
    >>> a = uuid7()
    >>> b = uuid7()
    >>> compare(a, b)
    -1
  """
  ia, ib = _to_int(a), _to_int(b)
  if ia < ib: return -1
  if ia > ib: return +1
  return 0

def sort(uuids: list[str], *, reverse: bool = False) -> list[str]:
  """
  Return *uuids* sorted chronologically, oldest first by default.

  Args:
    uuids:   list of UUID v7 strings to sort.
    reverse: if True, sort newest first

  Raises:
    InvalidUUIDError - if any string in the list is not a valid UUID v7.

  Example:
    >>> ids = batch(5)
    >>> ids == sort(ids)
    True
  """
  return sorted(uuids, key=_to_int, reverse=reverse)
