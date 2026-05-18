"""
pendulumium - UUID v7 generator (RFC 9562)

Time-sorted, nanosecond-precise, collision-resistant.

Quick start:
  from pendulumium import uuid7, decode, to_datetime

  uid = uuid7()
  decode(uid)      # full field breakdown
  to_datetime(uid) # datetime(2026, ..., tzinfo=UTC)
"""

from .exceptions import (
  PendulumiumError,
  ClockRollbackError,
  InvalidUUIDError
)
from ._generator import Pendulumium
from ._decoder import decode, to_datetime, to_unix_ms
from ._validator import is_valid, is_v7

uuid7 = Pendulumium.uuid7

__all__ = [
  # generation
  "uuid7",
  "Pendulumium",
  # decoding
  "decode",
  "to_datetime",
  "to_unix_ms",
  # validation
  "is_valid",
  "is_v7",
  # exceptions
  "PendulumiumError",
  "ClockRollbackError",
  "InvalidUUIDError",
]

__version__ = "2.0.0"