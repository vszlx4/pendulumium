"""
inspection/pretty.py - human-readable UUID v7 breakdown for terminal output.
"""

from __future__ import annotations
from typing import cast

import datetime

from .decoder import decode


def pretty(uuid: str, *, print_output: bool = True) -> dict[str, object]:
  """
  Print a human-readable breakdown of every field in a UUID v7 string.

  Args:
    uuid:         UUID v7 string to inspect.
    print_output: if True (default), prints to stdout.
                  if False, returns the dict silently.

  Returns:
    The same dict as decode(), for programmatic use.

  Raises:
    InvalidUUIDError - if the string is not a valid UUID v7.

  Example:
    >>> pretty("019e2c01-6909-7583-800a-8afe60572a94")

    019e2c01-6909-7583-800a-8afe60572a94

      timestamp   2026-05-15 14:19:10.473 UTC
      sub-ms      ~342 µs into that millisecond
      version     7
      variant     0b10 (RFC 9562)
      sequence    10
      node ID     0x800a
      entropy     0x2afe6057
  """
  info = decode(uuid)

  dt        = cast(datetime.datetime, info["datetime_utc"])
  ts_ms     = cast(int, info["timestamp_ms"])
  sub_ms_ns = cast(int, info["sub_ms_ns"])
  version   = cast(int, info["version"])
  variant   = cast(str, info["variant"])
  sequence  = cast(int, info["sequence"])
  node_id   = cast(int, info["node_id"])
  entropy   = cast(int, info["entropy"])

  sub_ms_us = sub_ms_ns // 1_000

  if print_output:
    print(f"\n  {uuid}\n")
    print(f"  {'timestamp':<12} {dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} UTC  ({ts_ms} ms)")
    print(f"  {'sub-ms':<12} ~{sub_ms_us} µs into that millisecond")
    print(f"  {'version':<12} {version}")
    print(f"  {'variant':<12} {variant}")
    print(f"  {'sequence':<12} {sequence}")
    print(f"  {'node ID':<12} {hex(node_id)}")
    print(f"  {'entropy':<12} {hex(entropy)}")
    print()

  return info