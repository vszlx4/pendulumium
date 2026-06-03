"""
pendulumium - UUID v7 generator (RFC 9562)

Time-sorted, nanosecond-precise, collision-resistant.

Quick start:
  from pendulumium import uuid7, decode, to_datetime

  uid = uuid7()
  decode(uid)      # full field breakdown
  to_datetime(uid) # datetime(2026, ..., tzinfo=UTC)
"""

from .core.exceptions      import (
  PendulumiumError,
  ClockRollbackError,
  InvalidUUIDError
)
from .core.generator       import Pendulumium
from .core.batch           import batch
from .core.stream          import stream
from .inspection.decoder   import decode, to_datetime, to_unix_ms
from .inspection.validator import is_valid, is_v7
from .inspection.compare   import compare, sort
from .inspection.pretty    import pretty
from .utils.convert        import to_hex, to_int, to_bytes, from_int, from_bytes
from .utils.time           import age, between, from_datetime, from_unix_ms


uuid7 = Pendulumium.uuid7

__all__ = [
  # generation
  "uuid7",
  "Pendulumium",  # exposes .generate(), .stats(), .on_clock_rollback()
  # decoding
  "decode",
  "to_datetime",
  "to_unix_ms",
  # validation
  "is_valid",
  "is_v7",
  # comparison
  "compare",
  "sort",
  # conversion
  "to_hex",
  "to_int",
  "to_bytes",
  "from_int",
  "from_bytes",
  # batch
  "batch",
  # time
  "age",
  "between",
  "from_datetime",
  "from_unix_ms",
  # pretty
  "pretty",
  # stream
  "stream",
  # exceptions
  "PendulumiumError",
  "ClockRollbackError",
  "InvalidUUIDError",
]

__version__ = "3.0.0"
