"""
pendulumium - UUID v7 generator (RFC 9562)

Time-sorted, nanosecond-precise, collision-resistant identifiers
built on the 2024 IETF standard. Zero runtime dependencies.

Install:
  pip install git+https://github.com/vszlx4/pendulumium.git

Quick start:
  from pendulumium import uuid7, decode, to_datetime, batch, stream

  uid = uuid7()                    # "019e2c01-6909-7583-800a-8afe60572a94"
  decode(uid)                      # full field breakdown — timestamp, node, entropy, etc.
  to_datetime(uid)                 # datetime(2026, ..., tzinfo=UTC)
  batch(1_000)                     # 1000 monotonic UUIDs in one call
  for uid in stream():             # lazy infinite iterator
    process(uid)

Generation:
  uuid7()                          # single UUID v7 string
  batch(n)                         # n UUIDs, one lock acquisition
  stream(n)                        # lazy iterator, finite or infinite
  Pendulumium(node_id=0xAB12)      # scoped generator with explicit node ID
  Pendulumium.stats()              # generation state snapshot
  Pendulumium.on_clock_rollback()  # register clock drift callback

Inspection:
  decode(uid)                      # all fields as a dict
  to_datetime(uid)                 # UTC-aware datetime
  to_unix_ms(uid)                  # Unix milliseconds
  pretty(uid)                      # human-readable terminal breakdown
  is_valid(uid)                    # format check (any UUID version)
  is_v7(uid)                       # format + version + variant check
  compare(a, b)                    # chronological comparison, returns -1/0/+1
  sort(uuids)                      # sort list oldest to newest
  check_collisions(uuids)          # detect and report duplicates
  find_gaps(uuids, threshold_ms)   # find time gaps in a sorted list

Time utilities:
  age(uid)                         # timedelta since creation
  between(uid, start, end)         # was this ID created in a time window?
  from_datetime(dt)                # generate UUID rooted at a past datetime
  from_unix_ms(ms)                 # generate UUID rooted at a past Unix ms
  between_times(start, end, n)     # n UUIDs spread across a time range

Conversion:
  to_hex(uid)                      # 32-char hex string, no hyphens
  to_int(uid)                      # 128-bit integer
  to_bytes(uid)                    # 16 raw bytes, big-endian
  from_int(value)                  # int to UUID string
  from_bytes(data)                 # bytes to UUID string

SQL & integration:
  sql_range(start, end)            # (lower, upper) boundaries for BETWEEN queries
  emit_types()                     # emit TypeScript branded UUIDv7 type definition

Benchmarking:
  from pendulumium.bench import run, profile
  run(100_000)                     # generation + decode + collision report
  profile(5.0)                     # sustained throughput over fixed duration
"""

from .core.exceptions       import (
  PendulumiumError,
  ClockRollbackError,
  InvalidUUIDError
)
from .core.generator        import Pendulumium
from .core.batch            import batch
from .core.stream           import stream
from .inspection.decoder    import decode, to_datetime, to_unix_ms
from .inspection.validator  import is_valid, is_v7
from .inspection.compare    import compare, sort
from .inspection.pretty     import pretty
from .inspection.collisions import check_collisions
from .inspection.gaps       import find_gaps
from .utils.convert         import to_hex, to_int, to_bytes, from_int, from_bytes
from .utils.time            import age, between, from_datetime, from_unix_ms, between_times
from .utils.sql             import sql_range
from .utils.types           import emit_types
from .                      import bench


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
  "between_times",
  # pretty
  "pretty",
  # stream
  "stream",
  # collisions
  "check_collisions",
  # gaps
  "find_gaps",
  # sql
  "sql_range",
  # types
  "emit_types",
  # bench (use as: pendulumium.bench.run(), pendulumium.bench.profile())
  "bench",
  # exceptions
  "PendulumiumError",
  "ClockRollbackError",
  "InvalidUUIDError",
]

__version__ = "3.0.0"
