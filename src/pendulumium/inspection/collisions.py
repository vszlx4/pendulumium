"""
inspection/collisions.py - duplicate detection for UUID v7 lists.

  check_collisions(uuids) - detect and report duplicate UUIDs in a list
"""

from __future__ import annotations

from .validator import is_v7
from ..core.exceptions import InvalidUUIDError


def check_collisions(uuids: list[str]) -> dict[str, object]:
  """
  Detect duplicate UUIDs in a list and report their positions.

  Args:
    uuids: list of UUID v7 strings to check.

  Returns:
    A dict with keys:
      total      - total number of UUIDs checked (int)
      collisions - number of UUIDs that appear more than once (int)
      duplicates - list of dicts, each with:
        uuid      - the duplicate UUID string
        positions - list of indexes where it appears
  
  Raises:
    InvalidUUIDError - if any string in the list is not a valid UUID v7.
    ValueError       - if the list is empty.

  Example:
    >>> ids = batch(1_000_000)
    >>> result = check_collisions(ids)
    >>> result["collisions"]
    0
  """
  if not uuids:
    raise ValueError("uuids list must not be empty.")
  
  for uid in uuids:
    if not is_v7(uid):
      raise InvalidUUIDError(uid)
  
  seen: dict[str, list[int]] = {}
  for index, uid in enumerate(uuids):
    normalized = uid.lower()
    if normalized not in seen:
      seen[normalized] = []
    seen[normalized].append(index)
  
  duplicates = [
    {"uuid": uid, "positions": positions}
    for uid, positions in seen.items()
    if len(positions) > 1
  ]

  return {
    "total":      len(uuids),
    "collisions": len(duplicates),
    "duplicates": duplicates
  }
