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
  """