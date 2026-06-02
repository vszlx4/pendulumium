"""
_convert.py - format conversion utilities for UUID v7 strings.

Converts between the four representations:
  - hyphenated string  "019e2c01-6909-7583-800a-8afe60572a94"  (default)
  - raw hex string     "019e2c016909758380 0a8afe60572a94"
  - 128-bit integer    32141683943494588...
  - 16 bytes           b'\x01\x9e...'
"""

from __future__ import annotations

from .exceptions import InvalidUUIDError
from ._validator import is_valid


def _clean(uuid: str) -> str:
  """Strip hyphens and validate format, raising InvalidUUIDError if malformed."""
  if not is_valid(uuid):
    raise InvalidUUIDError(uuid, "does not match 8-4-4-4-12 UUID format")
  return uuid.replace("-", "")


def to_hex(uuid: str) -> str:
  """
  Return the UUID as a 32-character hex string without hyphens.

  Raises:
    InvalidUUIDError - if the string is not a well-formed UUID.

  Example:
    >>> to_hex("019e2c01-6909-7583-800a-8afe60572a94")
    "019e2c016909758380 0a8afe60572a94"
  """
  return _clean(uuid)


def to_int(uuid: str) -> int:
  """
  Return the UUID as a 128-bit integer.

  Raises:
    InvalidUUIDError - if the string is not a well-formed UUID.

  Example:
    >>> to_int("019e2c01-6909-7583-800a-8afe60572a94")
    2140668552...
  """
  return int(_clean(uuid), 16)


def to_bytes(uuid: str) -> bytes:
  """
  Return the UUID as 16 raw bytes, big-endian.

  Suitable for PostgreSQL native uuid columns, Protobuf,
  and any binary protocol that stores UUIDs as raw bytes.

  Raises:
    InvalidUUIDError - if the string is not a well-formed UUID.

  Example:
    >>> to_bytes("019e2c01-6909-7583-800a-8afe60572a94")
    b'\\x01\\x9e...'
  """
  return int(_clean(uuid), 16).to_bytes(16, "big")


def from_int(value: int, formatted: bool = True) -> str:
  """
  Convert a 128-bit integer to a UUID string.

  Args:
    value:     128-bit integer representing a UUID.
    formatted: if True (default), returns hyphenated 8-4-4-4-12 string.
               if False, returns raw 32-character hex string.

  Raises:
    ValueError - if value is out of range for a 128-bit integer.

  Example:
    >>> from_int(to_int(uid)) == uid
    True
  """
  if not (0 <= value < (1 << 128)):
    raise ValueError(
      f"Value {value} is out of 128-bit range."
    )
  h = f"{value:032x}"
  return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}" if formatted else h


def from_bytes(data: bytes, formatted: bool = True) -> str:
  """
  Convert 16 raw bytes to a UUID string.

  Args:
    data: exactly 16 bytes, big-endian.
    formatted: if True (default), return a hyphenated 8-4-4-4-12 string.
               if False, returns raw 32-character hex string.

  Raises:
    ValueError - if data is not exactly 16 bytes.

  Example:
    >>> from_bytes(to_bytes(uid)) == uid
    True
  """
  if len(data) != 16:
    raise ValueError(
      f"Expected 16 bytes, got {len(data)}."
    )
  return from_int(int.from_bytes(data, "big"), formatted)