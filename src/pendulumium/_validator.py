"""
_validator.py - format and version validation for UUID v7

Used internally by _decoder.py, _compare.py, and _convert.py
to guard their inputs, and exported publicly for API-boundry validaton.
"""

from __future__ import annotations

import re

_UUID_RE = re.compile(
  r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
  re.IGNORECASE,
)

def is_valid(uuid: str) -> bool:
  """
  Return True if *uuid* is a well-formed UUID string (any version).

  Only checks format - 8-4-4-4-12 hex groups with hyphens.
  Does not check version or variant bits.

  Example:
    >>> is_valid("019e2c01-6909-7583-800a-8afe60572a94")
    True
    >>> is_valid("not-a-uuid")
    False
  """
  return bool(_UUID_RE.match(uuid))

def is_v7(uuid: str) -> bool:
  """
  Return True if *uuid* is a well-formed UUID v7.

  Checks:
    - 8-4-4-4-12 format
    - version nibble == 7  (13th hex character)
    - variant bits == 0b10 (17th hex character, top two bits)

  Example:
    >>> is_v7("019e2c01-6909-7583-800a-8afe60572a94")
    True
    >>> is_v7("550e8400-e29b-41d4-a716-446655440000") # v4
    False
  """
  if not is_valid(uuid):
    return False

  clean           = uuid.replace("-", "")
  version_nibble  = int(clean[12], 16)
  variant_nibble  = int(clean[16], 16)

  return version_nibble == 7 and (variant_nibble >> 2) == 0b10