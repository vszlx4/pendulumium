"""
utils/time.py - time-based utilities for UUID v7 strings.

  age(uuid)                    - how old is this ID as a timedelta
  between(uuid, start, end)    - was this ID created within a time window
  from_datetime(dt)            - generate a UUID rooted at a past datetime
  from_unix_ms(ms)             - generate a UUID rooted at a past Unix ms timestamp
  between_times(start, end, n) - generate n UUIDs spread across a time range
"""

from __future__ import annotations
from typing import cast

import datetime
import secrets

from ..inspection.decoder import decode

def _to_ms(t: datetime.datetime | int) -> int:
  """
  Normalize a datetime or raw Unix milliseconds to an integer ms timestamp.

  Raises:
    TypeError - if t is neither a datetime nor an int.
  """
  if isinstance(t, datetime.datetime):
    return int(t.timestamp() * 1_000)
  if isinstance(t, int):
    return t
  raise TypeError(
    f"Expected datetime or int (Unix ms), got {type(t).__name__}"
  )


def _assemble(ts_ms: int) -> str:
  """
  Assemble a UUID v7 string from a given millisecond timestamp.

  Sub-ms, sequence, and node fields are zeroed.
  Entropy field is freshly randomized.
  Version and variant bits are set per RFC 9562.
  """
  ts      = ts_ms & ((1 << 48) - 1)
  entropy = secrets.randbits(32)

  uuid_int = (
    (ts     << 80)
    | (0x7    << 76)   # version = 7
    | (0b10   << 62)   # variant = 10xx
    | entropy
    ) & ((1 << 128) - 1)

  h = f"{uuid_int:032x}"
  return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


def age(uuid: str) -> datetime.timedelta:
  """
  Return how old a UUID v7 is as a timedelta from now (UTC).

  Raises:
    InvalidUUIDError - if the string is not a valid UUID v7.

  Example:
    >>> uid = uuid7()
    >>> age(uid).total_seconds() < 1
    True
  """
  ts_ms = decode(uuid)["timestamp_ms"]
  now_ms = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1_000)
  return datetime.timedelta(milliseconds=now_ms - cast(int, ts_ms))


def between(uuid: str, start: datetime.datetime | int, end: datetime.datetime | int) -> bool:
  """
  Return True if the UUID v7 was created within [start, end] inclusive.

  Args:
    uuid:  UUID v7 string to check.
    start: window start — UTC-aware datetime or Unix milliseconds (int).
    end:   window end   — UTC-aware datetime or Unix milliseconds (int).
  
  Raises:
    InvalidUUIDError - if the string is not a valid UUID v7.
    TypeError        - if start or end is not a datetime or int.
    ValueError       - if start > end.

  Example:
    >>> uid = uuid7()
    >>> now = datetime.datetime.now(tz=datetime.timezone.utc)
    >>> between(uid, now - timedelta(seconds=5), now)
    True
  """
  start_ms = _to_ms(start)
  end_ms   = _to_ms(end)

  if start_ms > end_ms:
    raise ValueError(
      f"start ({start_ms}ms) must not be after end ({end_ms}ms)"
    )
  
  ts_ms = cast(int, decode(uuid)["timestamp_ms"])
  return start_ms <= ts_ms <= end_ms


def from_datetime(dt: datetime.datetime) -> str:
  """
  Generate a UUID v7 rooted at a specific past UTC datetime.

  Useful for data migrations, seeding test fixtures, or reconstructing
  historical records. The entropy field is freshly randomized so two
  calls with the same datetime produce different UUIDs.

  Args:
    dt: a UTC-aware datetime. Must be in the past and after Unix epoch.

  Raises:
    TypeError  - if dt is not a datetime.
    ValueError - if dt is in the future or before the Unix epoch.
  
  Example:
    >>> dt = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
    >>> uid = from_datetime(dt)
    >>> to_datetime(uid).date() == dt.date()
    True
  """
  if not isinstance(dt, datetime.datetime):
    raise TypeError(f"Expected datetime, got {type(dt).__name__}.")
  
  if dt.tzinfo is None:
    raise ValueError(
      "datetime must be UTC-aware (tzinfo required). "
      "Use datetime.timezone.utc or a similar tzinfo."
    )
  
  now_ms = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1_000)
  ts_ms  = int(dt.timestamp() * 1_000)

  if ts_ms < 0:
    raise ValueError("datetime must be after the Unix epoch (1970-01-01 UTC).")
  
  if ts_ms > now_ms:
    raise ValueError(
      f"datetime is in the future ({dt.isoformat()}). "
      "from_datetime() only accepts past timestamps."
    )
  
  return _assemble(ts_ms)


def from_unix_ms(ms: int) -> str:
  """
  Generate a UUID v7 rooted at a specific past Unix millisecond timestamp.

  Useful when you already have a millisecond timestamp and don't want
  to convert it to a datetime first.

  Args:
    ms: Unix timestamp in milliseconds. Must be in the past and >= 0.

  Raises:
    TypeError  - if ms is not an int.
    ValueError - if ms is in the future or negative.

  Example:
    >>> uid = from_unix_ms(1_700_000_000_000)
    >>> to_unix_ms(uid) == 1_700_000_000_000
    True
  """
  if not isinstance(ms, int):
    raise TypeError(f"Expected int (Unix ms), got {type(ms).__name__}.")
  
  now_ms = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1_000)

  if ms < 0:
    raise ValueError("Timestamp must be >= 0 (after Unix epoch).")
  
  if ms > now_ms:
    raise ValueError(
      f"Timestamp {ms}ms is in the future. "
      "from_unix_ms() only accepts past timestamps."
    )
  
  return _assemble(ms)


def between_times(start: datetime.datetime | int, end: datetime.datetime | int, n: int) -> list[str]:
  """
  Generate *n* UUIDs with timestamps evenly distributed across [start, end].

  Useful for seeding test databases with realistic temporal spread rather
  than all IDs sharing the same creation timestamp.

  Args:
    start: range start — UTC-aware datetime or Unix milliseconds (int).
    end:   range end   — UTC-aware datetime or Unix milliseconds (int).
    n:     number of UUIDs to generate. Must be >= 1.

  Returns:
    List of UUID v7 strings in chronological order.

  Raises:
    TypeError  - if start or end is not a datetime or int.
    ValueError - if start >= end, n < 1, or either timestamp is
                 in the future or before the Unix epoch.

  Example:
    >>> start = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
    >>> end   = datetime.datetime(2026, 12, 31, tzinfo=datetime.timezone.utc)
    >>> ids   = between_times(start, end, n=1_000)
    >>> len(ids)
    1000
  """
  if n < 1:
    raise ValueError(f"n must be >= 1, got {n}.")
  
  start_ms = _to_ms(start)
  end_ms   = _to_ms(end)

  if start_ms < 0 or end_ms < 0:
    raise ValueError("Timestamps must be after the Unix epoch (>= 0).")
  
  now_ms = int(datetime.datetime.now(tz=datetime.timezone.utc).timestamp() * 1_000)

  if start_ms > now_ms or end_ms > now_ms:
    raise ValueError(
      "Both start and end must be in the past. "
      "between_times() only accepts past timestamps."
    )
  
  if start_ms >= end_ms:
    raise ValueError(
      f"start ({start_ms}ms) must be before end ({end_ms}ms)."
    )
  
  # evenly space n timestamps across [start_ms, end_ms]
  # n=1 gets the midpoint, n>1 gets evenly spaced including both endpoints
  if n == 1:
    timestamps = [start_ms + (end_ms - start_ms) // 2]
  else:
    step = (end_ms - start_ms) / (n - 1)
    timestamps = [int(start_ms + i * step) for i in range(n)]

  return [_assemble(ts) for ts in timestamps]
