"""
batch.py - efficient bulk UUID v7 generation.

Acquires the generator lock once for the entire batch rather than once
per ID, making bulk generation faster than calling uuid7() in a loop
and guaranteeing monotonic ordering across the whole batch.
"""

from __future__ import annotations

import secrets
import time

from .generator import Pendulumium


def batch(n: int, *, as_string: bool = True, formatted: bool = True) -> list[int | str]:
  """
  Generate *n* guaranteed-monotonic UUID v7 values in one call.

  Args:
    n:         number of UUIDs to generate. Must be >= 1.
    as_string: if True (default), returns hex strings.
               if False, returns 128-bit integers.
    formatted: if True (default), inserts RFC hyphens (8-4-4-4-12).
               ignored when as_string is False.

  Returns:
    List of UUIDs in chronological order.

  Raises:
    ValueError - if n < 1.

  Example:
    >>> ids = batch(1000)
    >>> ids == sort(ids)
    True
  """
  if n < 1:
    raise ValueError(f"n must be >= 1, got {n}.")

  results = []

  with Pendulumium._lock:
    for _ in range(n):
      ms, ns_rem = Pendulumium._now_ns()

      if ms == Pendulumium._last_ms:
        Pendulumium._counter += 1
        if Pendulumium._counter > 0x3FFF:
          while ms == Pendulumium._last_ms:
            ms, ns_rem = Pendulumium._now_ns()
            time.sleep(1e-6)
          Pendulumium._counter = 0
      else:
        if ms < Pendulumium._last_ms:
          raise RuntimeError(
            f"[!] Clock moved backwards: last={Pendulumium._last_ms} now={ms}"
          )
        Pendulumium._counter = 0

      Pendulumium._last_ms = ms
      Pendulumium._last_ns = ns_rem

      ts      = ms & ((1 << 48) - 1)
      sub_ms  = (ns_rem * 0xFFF) // 999_999
      seq     = Pendulumium._counter & 0x3FFF
      node    = Pendulumium._node_id
      entropy = secrets.randbits(32)

      uuid_int = (
          (ts      << 80)
        | (0x7     << 76)
        | (sub_ms  << 64)
        | (0b10    << 62)
        | (seq     << 48)
        | (node    << 32)
        | entropy
      ) & ((1 << 128) - 1)

      if not as_string:
        results.append(uuid_int)
      else:
        h = f"{uuid_int:032x}"
        results.append(
          f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}" if formatted else h
        )

  return results
