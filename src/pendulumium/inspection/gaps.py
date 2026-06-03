"""
inspection/gaps.py - time gap detection for sorted UUID v7 lists.

  find_gaps(uuids, threshold_ms) - find time gaps larger than a threshold
"""

from __future__ import annotations

from ..core.exceptions import InvalidUUIDError
from .validator import is_v7
from .decoder import decode
from typing import cast

def find_gaps(uuids: list[str], threshold_ms: int = 1_000) -> dict[str, object]:
  """
  Find time gaps larger than *threshold_ms* in a sorted list of UUID v7s.

  Useful for detecting dropped events, missed records, or holes in a 
  time-ordered log. The list must be in chronological order — pass it 
  through sort() first if unsure.

  Args:
    uuids:        list of UUID v7 strings in chronological order.
    threshold_ms: minimum gap size in milliseconds to report (default 1000).
                  Any two consecutive IDs with a timestamp difference
                  greater than this value will be included in the results.

  Returns:
    A dict with keys:
      total   - total number of UUIDs checked (int)
      gaps    - number of gaps found above the threshold (int)
      details - list of dicts, each with:
        before      - UUID just before the gap
        after       - UUID just after the gap
        gap_ms      - gap size in milliseconds (int)
        gap_seconds - gap size in seconds (int)
        index       - index of *before* in the original list
  
  Raises:
    InvalidUUIDError - if any string in the list is not a valid UUID v7.
    ValueError       - if the list has fewer than 2 items, or
                       threshold_ms is less than 1.

  Example:
    >>> ids = batch(100)
    >>> result = find_gaps(ids, threshold_ms=500)
    >>> result["gaps"]
    0
  """
  if len(uuids) < 2:
    raise ValueError("uuids must contain at least 2 items to find gaps.")
  
  if threshold_ms < 1:
    raise ValueError(f"threshold_ms must be >= 1, got {threshold_ms}.")
  
  for uid in uuids:
    if not is_v7(uid):
      raise InvalidUUIDError(uid)
  
  details = []

  for i in range(len(uuids) - 1):
    ts_a = cast(int, decode(uuids[i])["timestamp_ms"])
    ts_b = cast(int, decode(uuids[i + 1])["timestamp_ms"])
    gap  = ts_b - ts_a

    if gap > threshold_ms:
      details.append({
        "before": uuids[i],
        "after": uuids[i + 1],
        "gap_ms": gap,
        "gap_seconds": round(gap / 1_000, 3),
        "index": i
      })
  
  return {
    "total": len(uuids),
    "gaps": len(details),
    "details": details
  }
