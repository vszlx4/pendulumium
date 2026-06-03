"""
core/stream.py - lazy UUID v7 generator iterator.

Yields UUIDs one at a time rather than building a full list in memory,
making it suitable for large volumes or indefinite generation loops.
"""

from __future__ import annotations

from typing import Iterator

from .generator import Pendulumium


def stream(n: int | None = None, *, as_string: bool = True, formatted: bool = True) -> Iterator[int | str]:
  """
  Lazily yield UUID v7 values one at a time.

  Unlike batch(), no list is built in memory — each ID is generated
  and yielded on demand. Suitable for large volumes or infinite loops.

  Args:
    n:         number of UUIDs to yield. If None (default), yields forever.
    as_string: if True (default), yields hex strings.
               if False, yields 128-bit integers.
    formatted: if True (default), inserts RFC hyphens (8-4-4-4-12).
               ignored when as_string is False

  Raises:
    ValueError - if n is not None and n < 1.

  Example:
    >>> for uid in stream(5):
    ...   print(uid)

    >>> for uid in stream():
    ...   process(uid)
    ...   if done: break
  """
  if n is not None and n < 1:
    raise ValueError(f"n must be >= 1 or None, got {n}")
  
  if n is None:
    while True:
      yield Pendulumium.uuid7(as_string=as_string, formatted=formatted)
  else:
    for _ in range(n):
      yield Pendulumium.uuid7(as_string=as_string, formatted=formatted)