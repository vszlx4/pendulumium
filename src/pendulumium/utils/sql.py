"""
utils/sql.py - SQL query helper utilities for UUID v7.

  sql_range(start, end) - return UUID v7 boundary values for a SQL BETWEEN clause
"""

from __future__ import annotations

import datetime

from ..core.exceptions import InvalidUUIDError
from ..inspection.validator import is_v7


def _boundary(ts_ms: int, high: bool) -> str:
  """
  Build a UUID v7 boundary string for a given millisecond timestamp.

  For the lower boundary (high=False): sub-ms, sequence, node, and 
  entropy fields are all set to 0x00 — the smallest possible UUID 
  for that millisecond.

  For the upper boundary (high=True): sub-ms, sequence, node, and 
  entropy fields are all set to 0xFF / max — the largest possible 
  UUID for that millisecond.
  """
  ts = ts_ms & ((1 << 48) - 1)

  if not high:
    uuid_int = (
      (ts   << 80)
      | (0x7  << 76) # version = 7
      | (0b10 << 62) # variant = 10xx
    ) & ((1 << 128) - 1)
  else:
    uuid_int = (
      (ts        << 80)
      | (0x7       << 76) # version = 7
      | (0xFFF     << 64) # sub-ms: max
      | (0b10      << 62) # variant = 10xx
      | (0x3FFF    << 48) # sequence: max
      | (0xFFFF    << 32) # node: max
      | (0xFFFFFFFF)      # entropy: max
    ) & ((1 << 128) - 1)

  h = f"{uuid_int:032x}"
  return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


def sql_range(start: datetime.datetime | int, end: datetime.datetime | int) -> tuple[str, str]:
  """
  Return UUID v7 boundary values for a SQL BETWEEN query.

  Since UUID v7 embeds the timestamp in the most significant bits,
  you can query a time range using the primary key column directly
  — no separate created_at column needed.

  Args:
    start: range start — UTC-aware datetime or Unix milliseconds (int).
    end:   range end   — UTC-aware datetime or Unix milliseconds (int).
    
  Returns:
    A tuple (lower, upper) of UUID v7 strings where:
      lower - smallest possible UUID v7 for the start millisecond
      upper - largest possible UUID v7 for the end millisecond

  Raises:
    TypeError  - if start or end is not a datetime or int.
    ValueError - if start >= end or either timestamp is negative.

  Example:
    >>> lower, upper = sql_range(
    ...     datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),
    ...     datetime.datetime(2026, 12, 31, tzinfo=datetime.timezone.utc),
    ... )
    >>> f"WHERE id BETWEEN '{lower}' AND '{upper}'"
    "WHERE id BETWEEN '01938a8c-...' AND '01972f4b-...'"
  """
  def to_ms(t: datetime.datetime | int) -> int:
    if isinstance(t, datetime.datetime):
      return int(t.timestamp() * 1_000)
    if isinstance(t, int):
      return t
    raise TypeError(
      f"Expected datetime or int (Unix ms), got {type(t).__name__}."
    )
  
  start_ms = to_ms(start)
  end_ms   = to_ms(end)

  if start_ms < 0 or end_ms < 0:
    raise ValueError("Timestamps must be >= 0 (after Unix epoch).")
  
  if start_ms >= end_ms:
    raise ValueError(
      f"start ({start_ms}ms) must be before end ({end_ms}ms)."
    )
  
  return _boundary(start_ms, high=False), _boundary(end_ms, high=True)
