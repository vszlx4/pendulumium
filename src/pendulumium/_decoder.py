"""
_decoder.py - parse a UUID v7 back into its constituent fields.

Mirrors the exact bit layout from _generator.py:

  [127:80]  48 bits  Unix timestamp in milliseconds
  [79:76]    4 bits  Version (always 7)
  [75:64]   12 bits  Sub-ms bucket, scaled via (ns_rem * 0xFFF) // 999_999
  [63:62]    2 bits  Variant (always 0b10)
  [61:48]   14 bits  Monotonic sequence counter
  [47:32]   16 bits  Node ID
  [31:0]    32 bits  Cryptographic entropy
"""

from __future__ import annotations

import datetime
import re

from .exceptions import InvalidUUIDError

_UUID_RE = re.compile(
  r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
  re.IGNORECASE
)


def _validate_v7(uuid: str) -> int:
  """
  Parse *uuid* into a 128-bit integer, raising InvalidUUIDError if:
    - the string isn't a well-formed UUID
    - the version nibble isn't 7
    - the variant bits aren't 0b10
  """
  if not _UUID_RE.match(uuid):
    raise InvalidUUIDError(uuid, "does not match 8-4-4-4-12 UUID format")

  clean    = uuid.replace("-", "")
  uuid_int = int(clean, 16)

  version = (uuid_int >> 76) & 0xF
  if version != 7:
    raise InvalidUUIDError(uuid, f"version nibble is {version}, expected 7")
  
  variant = (uuid_int >> 62) & 0b11
  if variant != 0b10:
    raise InvalidUUIDError(uuid, f"variant bits are {variant:#04b}, expected 0b10")
  
  return uuid_int

def decode(uuid: str) -> dict[str, object]:
  """
  Parse a UUID v7 string into all of its constituent fields.

  Returns a dict with keys:
    uuid         - normalized hyphenated string (lowercase)
    uuid_int     - 128-bit integer
    timestamp_ms - Unix milliseconds (int)
    timestamp_ns - approximate Unix nanoseconds (int)
    datetime_utc - UTC-aware datetime
    version      - int, always 7
    variant      - str, always '0b10 (RFC 9562)'
    sub_ms       - 12-bit nanosecond-remainder bucket (0-4095)
    sub_ms_ns    - approximate nanosecond offset within the millisecond
    sequence     - 14-bit monotonic counter (0-16383)
    node_id      - 16-bit node identifier (int)
    entropy      - 32-bit cryptographic random field (int)

  Raises:
    InvalidUUIDError - if the string is not a valid UUID v7.
  """
  uuid_int = _validate_v7(uuid)

  ts_ms  = (uuid_int >> 80) & ((1 << 48) - 1) # [127:80]
  sub_ms = (uuid_int >> 64) & 0xFFF           # [75:64]
  seq    = (uuid_int >> 48) & 0x3FFF          # [61:48]
  node   = (uuid_int >> 32) & 0xFFFF          # [47:32]
  entropy =  uuid_int       & 0xFFFF_FFFF     # [31:0]

  # reverse the generator's scaling: (ns_rem * 0xFFF) // 999_999
  sub_ms_ns = (sub_ms * 999_999) // 0xFFF

  ts_ns = ts_ms * 1_000_000 + sub_ms_ns

  dt = datetime.datetime.fromtimestamp(
    ts_ms / 1_000,
    tz=datetime.timezone.utc
  )

  h          = f"{uuid_int:032x}"
  normalized = f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"

  return {
    "uuid": normalized,
    "uuid_int": uuid_int,
    "timestamp_ms": ts_ms,
    "timestamp_ns": ts_ns,
    "datetime_utc": dt,
    "version": 7,
    "variant": "0b10 (RFC 9562)",
    "sub_ms": sub_ms,
    "sub_ms_ns": sub_ms_ns,
    "sequence": seq,
    "node_id": node,
    "entropy": entropy
  }

def to_datetime(uuid: str) -> datetime.datetime:
  """
  Extract the creation time of a UUID v7 as a UTC-aware datetime.

  Raises:
    InvalidUUIDError - if the string is not a valid UUID v7.
  """
  return decode(uuid)["datetime_utc"] # type: ignore[return-value]

def to_unix_ms(uuid: str) -> int:
  """
  Extract the creation time of a UUID v7 as Unix milliseconds.

  Raises:
    InvalidUUIDError - if the string is not a valid UUID v7.
  """
  return decode(uuid)["timestamp_ms"] # type: ignore[return-value]