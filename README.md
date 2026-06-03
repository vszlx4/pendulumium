# pendulumium

**UUID v7 generator for Python — RFC 9562 compliant, time-sorted, nanosecond-precise, collision-resistant.**

Built on the 2024 IETF standard. Zero runtime dependencies. Python 3.10+.

```python
from pendulumium import uuid7, decode, to_datetime

uid = uuid7()
# "019e2c01-6909-7583-800a-8afe60572a94"

decode(uid)
# {
#   "timestamp_ms": 1778854750473,
#   "datetime_utc": datetime(2026, 5, 15, 14, 19, 10, tzinfo=UTC),
#   "version":      7,
#   "sequence":     3,
#   "node_id":      42139,
#   "entropy":      1340432471,
#   ...
# }

to_datetime(uid)
# datetime(2026, 5, 15, 14, 19, 10, tzinfo=timezone.utc)
```

---

## Table of contents

- [Why UUID v7?](#why-uuid-v7)
- [Install](#install)
- [Quick start](#quick-start)
- [Bit layout](#bit-layout)
- [API reference](#api-reference)
  - [Generation](#generation)
  - [Inspection](#inspection)
  - [Validation](#validation)
  - [Comparison and sorting](#comparison-and-sorting)
  - [Time utilities](#time-utilities)
  - [Format conversion](#format-conversion)
  - [SQL integration](#sql-integration)
  - [TypeScript integration](#typescript-integration)
  - [Benchmarking](#benchmarking)
- [Advanced usage](#advanced-usage)
  - [Scoped generators](#scoped-generators)
  - [Clock rollback handling](#clock-rollback-handling)
  - [Generator stats](#generator-stats)
- [Caveats](#caveats)
- [Running tests](#running-tests)
- [License](#license)

---

## Why UUID v7?

UUID v4 is the most common identifier format today — but it is **pure random**. Two IDs generated one millisecond apart look nothing alike, which means your database index has to jump all over the place on every insert. At scale this causes index fragmentation, slower writes, and degraded read performance.

UUID v7 solves this by putting a **Unix millisecond timestamp in the most significant bits**. IDs generated close together sort close together, which means:

- **B-tree indexes stay compact** — new rows land near the end, not scattered randomly
- **Range queries become cheap** — `WHERE id BETWEEN lower AND upper` uses the primary key index directly, no secondary `created_at` column needed
- **IDs are self-describing** — you can extract the creation time from the ID itself

| Property | UUID v4 | UUID v7 (pendulumium) |
|---|---|---|
| Chronologically sortable | ✗ | ✓ |
| Database index locality | ✗ | ✓ |
| Extract creation time from ID | ✗ | ✓ |
| RFC standard | ✓ RFC 4122 | ✓ RFC 9562 (2024) |
| Sub-millisecond precision | ✗ | ✓ nanoseconds |
| Thread-safe generation | depends | ✓ |
| Zero runtime dependencies | ✓ | ✓ |

---

## Install

```bash
# from GitHub
pip install git+https://github.com/vszlx4/pendulumium.git

# pin a specific release
pip install git+https://github.com/vszlx4/pendulumium.git@v3.0.0

# for local development
git clone https://github.com/vszlx4/pendulumium.git
cd pendulumium
pip install -e ".[dev]"
```

**Requirements:** Python 3.10 or later. No runtime dependencies.

---

## Quick start

```python
from pendulumium import uuid7, batch, decode, to_datetime, pretty

# generate one ID
uid = uuid7()
# "019e2c01-6909-7583-800a-8afe60572a94"

# generate 1000 IDs efficiently
ids = batch(1_000)

# parse every field out of an ID
info = decode(uid)
print(info["datetime_utc"])  # datetime(2026, ..., tzinfo=UTC)
print(info["sequence"])      # monotonic counter within that millisecond
print(info["node_id"])       # 16-bit node identifier

# human-readable terminal breakdown
pretty(uid)
#
#   019e2c01-6909-7583-800a-8afe60572a94
#
#   timestamp    2026-05-15 14:19:10.473 UTC  (1778854750473 ms)
#   sub-ms       ~342 µs into that millisecond
#   version      7
#   variant      0b10 (RFC 9562)
#   sequence     3
#   node ID      0xa47b
#   entropy      0x4fb3c219
```

---

## Bit layout

Every UUID v7 is 128 bits assembled as follows:

```
019e2c01-6909-7583-800a-8afe60572a94
├──────┤ ├──┤ ├──┤ ├──┤├───────────┤
timestamp  v7  sm   sq   node + entropy
48 bits    4b  12b  14b  16b  +  32b
```

| Field | Bits | Position | Description |
|---|---|---|---|
| Timestamp | 48 | `[127:80]` | Unix milliseconds since epoch |
| Version | 4 | `[79:76]` | Always `0111` (= 7) per RFC 9562 |
| Sub-ms | 12 | `[75:64]` | Nanosecond remainder scaled to 12 bits |
| Variant | 2 | `[63:62]` | Always `10` per RFC 9562 |
| Sequence | 14 | `[61:48]` | Monotonic counter, resets each millisecond |
| Node ID | 16 | `[47:32]` | SHA-256(PID + hostname), truncated |
| Entropy | 32 | `[31:0]` | Cryptographic random via `secrets.randbits` |

**Reading a UUID v7 by hand:**

```
019e2c01-6909-7583-800a-8afe60572a94
              ↑    ↑
              │    └── 17th char: 8 = 0b1000, top 2 bits = 10 → valid variant
              └── 13th char: always "7" → version 7
```

The first 12 hex characters are the timestamp:

```python
int("019e2c016909", 16)
# 1778854750473 ms → 2026-05-15 14:19:10 UTC
```

---

## API reference

### Generation

#### `uuid7(as_string=True, formatted=True) -> str | int`

Generate a single UUID v7. This is the primary entry point for most use cases.

```python
from pendulumium import uuid7

uid = uuid7()
# "019e2c01-6909-7583-800a-8afe60572a94"

uid = uuid7(formatted=False)
# "019e2c0169097583800a8afe60572a94"  (no hyphens)

uid = uuid7(as_string=False)
# 2140668552...  (128-bit integer)
```

IDs generated by `uuid7()` are guaranteed to be monotonically increasing within a single process, thread-safe, and RFC 9562 compliant.

---

#### `batch(n, *, as_string=True, formatted=True) -> list[str | int]`

Generate `n` UUIDs in one call. Acquires the generator lock **once** for the entire batch, making it significantly faster than calling `uuid7()` in a loop.

```python
from pendulumium import batch

ids = batch(10_000)
ids = batch(10_000, as_string=False)  # list of integers
```

The entire batch is guaranteed to be monotonically ordered.

---

#### `stream(n=None, *, as_string=True, formatted=True) -> Iterator[str | int]`

Lazily yield UUID v7s one at a time. Unlike `batch()`, no list is built in memory — each ID is generated on demand. Pass `n` for a finite stream, or omit it for an infinite iterator.

```python
from pendulumium import stream

# finite — process 1 million IDs without storing them all in RAM
for uid in stream(1_000_000):
    save_to_db(uid)

# infinite — runs until you break
for uid in stream():
    process(uid)
    if done:
        break
```

---

### Inspection

#### `decode(uuid) -> dict[str, object]`

Parse every field out of a UUID v7 string. Returns a dict with the following keys:

| Key | Type | Description |
|---|---|---|
| `uuid` | `str` | Normalized lowercase hyphenated string |
| `uuid_int` | `int` | 128-bit integer representation |
| `timestamp_ms` | `int` | Unix milliseconds |
| `timestamp_ns` | `int` | Approximate Unix nanoseconds |
| `datetime_utc` | `datetime` | UTC-aware datetime |
| `version` | `int` | Always `7` |
| `variant` | `str` | Always `"0b10 (RFC 9562)"` |
| `sub_ms` | `int` | 12-bit nanosecond bucket (0–4095) |
| `sub_ms_ns` | `int` | Approximate nanosecond offset within the millisecond |
| `sequence` | `int` | 14-bit monotonic counter (0–16383) |
| `node_id` | `int` | 16-bit node identifier |
| `entropy` | `int` | 32-bit cryptographic random field |

```python
from pendulumium import decode

info = decode("019e2c01-6909-7583-800a-8afe60572a94")
print(info["datetime_utc"])   # 2026-05-15 14:19:10.473000+00:00
print(info["sequence"])       # 3
print(info["node_id"])        # 42139
```

Raises `InvalidUUIDError` if the string is not a valid UUID v7.

---

#### `to_datetime(uuid) -> datetime`

Extract the creation time as a UTC-aware `datetime`. Shorthand for `decode(uuid)["datetime_utc"]`.

```python
from pendulumium import uuid7, to_datetime

uid = uuid7()
dt  = to_datetime(uid)
# datetime(2026, 5, 15, 14, 19, 10, 473000, tzinfo=timezone.utc)
```

---

#### `to_unix_ms(uuid) -> int`

Extract the creation time as Unix milliseconds. Shorthand for `decode(uuid)["timestamp_ms"]`.

```python
from pendulumium import uuid7, to_unix_ms

uid = uuid7()
ms  = to_unix_ms(uid)
# 1778854750473
```

---

#### `pretty(uuid, *, print_output=True) -> dict[str, object]`

Print a human-readable breakdown of every field to stdout. Returns the same dict as `decode()` for programmatic use. Pass `print_output=False` to suppress output and only get the dict.

```python
from pendulumium import uuid7, pretty

pretty(uuid7())
#
#   019e2c01-6909-7583-800a-8afe60572a94
#
#   timestamp    2026-05-15 14:19:10.473 UTC  (1778854750473 ms)
#   sub-ms       ~342 µs into that millisecond
#   version      7
#   variant      0b10 (RFC 9562)
#   sequence     3
#   node ID      0xa47b
#   entropy      0x4fb3c219
```

---

#### `check_collisions(uuids) -> dict[str, object]`

Detect and report any duplicate UUIDs in a list. Useful for stress-testing your generation setup.

```python
from pendulumium import batch, check_collisions

ids    = batch(1_000_000)
result = check_collisions(ids)

print(result["total"])      # 1000000
print(result["collisions"]) # 0
print(result["duplicates"]) # []
```

If duplicates exist, each entry in `duplicates` has `uuid`, and `positions` (list of indexes where it appeared).

---

#### `find_gaps(uuids, threshold_ms=1000) -> dict[str, object]`

Find time gaps larger than `threshold_ms` milliseconds in a sorted list of UUID v7s. Useful for detecting dropped events or holes in a time-ordered log.

```python
from pendulumium import find_gaps
from pendulumium.utils.time import between_times
import datetime

UTC      = datetime.timezone.utc
cluster_a = between_times(datetime.datetime(2026, 1, 1, tzinfo=UTC),
                          datetime.datetime(2026, 1, 2, tzinfo=UTC), n=100)
cluster_b = between_times(datetime.datetime(2026, 6, 1, tzinfo=UTC),
                          datetime.datetime(2026, 6, 2, tzinfo=UTC), n=100)

result = find_gaps(cluster_a + cluster_b, threshold_ms=1_000)
print(result["gaps"])     # 1
print(result["details"])
# [{"before": "...", "after": "...", "gap_ms": 12960000000, "gap_seconds": 12960000.0, "index": 99}]
```

---

### Validation

#### `is_valid(uuid) -> bool`

Return `True` if the string is a well-formed UUID (any version). Checks format only — 8-4-4-4-12 hex groups with hyphens. Case-insensitive.

```python
from pendulumium import is_valid

is_valid("019e2c01-6909-7583-800a-8afe60572a94")  # True
is_valid("not-a-uuid")                            # False
is_valid("550e8400-e29b-41d4-a716-446655440000")  # True (v4 — format is valid)
```

---

#### `is_v7(uuid) -> bool`

Return `True` if the string is a well-formed UUID v7. Checks format, version nibble (`7`), and variant bits (`10xx`). Case-insensitive.

```python
from pendulumium import is_v7

is_v7("019e2c01-6909-7583-800a-8afe60572a94")  # True
is_v7("550e8400-e29b-41d4-a716-446655440000")  # False (v4)
is_v7("not-a-uuid")                            # False
```

---

### Comparison and sorting

#### `compare(a, b) -> int`

Compare two UUID v7 strings chronologically. Returns `-1` if `a` was created before `b`, `0` if identical, `+1` if `a` was created after `b`.

Because UUID v7 is designed so that lexicographic order equals chronological order, this is equivalent to integer comparison of the 128-bit values — no timestamp extraction needed.

```python
from pendulumium import uuid7, compare

a = uuid7()
b = uuid7()

compare(a, b)  # -1  (a was created before b)
compare(b, a)  # +1
compare(a, a)  #  0
```

---

#### `sort(uuids, *, reverse=False) -> list[str]`

Return a list of UUID v7 strings sorted chronologically, oldest first by default. Pass `reverse=True` for newest first.

```python
from pendulumium import batch, sort

ids = batch(1_000)

oldest_first = sort(ids)
newest_first = sort(ids, reverse=True)
```

---

### Time utilities

#### `age(uuid) -> timedelta`

Return how old a UUID v7 is as a `timedelta` from now (UTC).

```python
from pendulumium import uuid7, age
import time

uid = uuid7()
time.sleep(2)

a = age(uid)
print(a.total_seconds())  # ~2.0
```

---

#### `between(uuid, start, end) -> bool`

Return `True` if the UUID v7 was created within `[start, end]` inclusive. Both `start` and `end` accept a UTC-aware `datetime` or Unix milliseconds as an `int`.

```python
from pendulumium import uuid7, between
import datetime

uid = uuid7()
now = datetime.datetime.now(tz=datetime.timezone.utc)

between(uid, now - datetime.timedelta(seconds=5), now)  # True

# also accepts raw milliseconds
between(uid, 1_700_000_000_000, 1_800_000_000_000)      # depends on when uid was created

# mix and match types
between(uid, now - datetime.timedelta(seconds=5), 9_999_999_999_999)  # True
```

---

#### `from_datetime(dt) -> str`

Generate a UUID v7 rooted at a specific past UTC datetime. The entropy field is freshly randomized so two calls with the same datetime produce different UUIDs.

Useful for data migrations, seeding test fixtures, or reconstructing historical records.

```python
from pendulumium import from_datetime, to_datetime
import datetime

dt  = datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc)
uid = from_datetime(dt)

to_datetime(uid).date()  # date(2025, 1, 1)

# two calls with the same datetime produce different IDs
from_datetime(dt) != from_datetime(dt)  # True
```

Raises `ValueError` if `dt` is in the future or before the Unix epoch. Raises `ValueError` if `dt` has no `tzinfo`.

---

#### `from_unix_ms(ms) -> str`

Generate a UUID v7 rooted at a specific past Unix millisecond timestamp. Equivalent to `from_datetime()` but skips the conversion step.

```python
from pendulumium import from_unix_ms, to_unix_ms

uid = from_unix_ms(1_700_000_000_000)
to_unix_ms(uid)  # 1700000000000
```

---

#### `between_times(start, end, n) -> list[str]`

Generate `n` UUIDs with timestamps evenly distributed across `[start, end]`. Useful for seeding test databases with realistic temporal spread.

```python
from pendulumium import between_times, to_datetime
import datetime

UTC   = datetime.timezone.utc
start = datetime.datetime(2026, 1,  1, tzinfo=UTC)
end   = datetime.datetime(2026, 12, 31, tzinfo=UTC)
ids   = between_times(start, end, n=1_000)

# IDs are evenly spaced across the year
to_datetime(ids[0]).month    # 1
to_datetime(ids[499]).month  # ~6
to_datetime(ids[999]).month  # 12
```

---

### Format conversion

#### `to_hex(uuid) -> str`

Return the UUID as a 32-character hex string without hyphens.

```python
to_hex("019e2c01-6909-7583-800a-8afe60572a94")
# "019e2c016909758380 0a8afe60572a94"
```

---

#### `to_int(uuid) -> int`

Return the UUID as a 128-bit integer.

```python
to_int("019e2c01-6909-7583-800a-8afe60572a94")
# 2140668552789123456789...
```

---

#### `to_bytes(uuid) -> bytes`

Return the UUID as 16 raw bytes, big-endian. This is the format expected by PostgreSQL's native `uuid` column, Protobuf, and most binary protocols.

```python
to_bytes("019e2c01-6909-7583-800a-8afe60572a94")
# b'\x01\x9e\x2c\x01\x69\x09\x75\x83\x80\x0a\x8a\xfe\x60\x57\x2a\x94'
```

---

#### `from_int(value, formatted=True) -> str`

Convert a 128-bit integer back to a UUID string.

```python
uid = uuid7(as_string=False)
from_int(uid)                   # "019e2c01-6909-7583-800a-8afe60572a94"
from_int(uid, formatted=False)  # "019e2c016909758380 0a8afe60572a94"
```

---

#### `from_bytes(data, formatted=True) -> str`

Convert 16 raw bytes back to a UUID string.

```python
b   = to_bytes(uid)
from_bytes(b)  # "019e2c01-6909-7583-800a-8afe60572a94"
```

---

### SQL integration

#### `sql_range(start, end) -> tuple[str, str]`

Return `(lower, upper)` UUID v7 boundary values for a SQL `BETWEEN` query. Since UUID v7 embeds the timestamp in the most significant bits, you can query by time range using the primary key column directly — no separate `created_at` column needed.

```python
from pendulumium import sql_range
import datetime

UTC   = datetime.timezone.utc
start = datetime.datetime(2026, 1,  1, tzinfo=UTC)
end   = datetime.datetime(2026, 12, 31, tzinfo=UTC)

lower, upper = sql_range(start, end)

# use in raw SQL
query = f"SELECT * FROM events WHERE id BETWEEN '{lower}' AND '{upper}'"

# use in SQLAlchemy
results = session.query(Event).filter(
    Event.id.between(lower, upper)
).all()
```

This replaces:
```sql
-- before: requires a secondary index on created_at
SELECT * FROM events WHERE created_at BETWEEN '2026-01-01' AND '2026-12-31'

-- after: uses the primary key index directly
SELECT * FROM events WHERE id BETWEEN '01930000-...' AND '0197ffff-...'
```

---

### TypeScript integration

#### `emit_types(*, print_output=True) -> str`

Emit a TypeScript branded `UUIDv7` type definition. The emitted code uses TypeScript's type branding pattern to enforce UUID v7 validity at compile time — a plain `string` cannot be passed where a `UUIDv7` is expected without an explicit cast, with zero runtime overhead.

```python
from pendulumium import emit_types

emit_types()                               # prints to stdout
code = emit_types(print_output=False)      # capture as string

with open("src/types/uuid.ts", "w") as f:
    f.write(code)
```

The emitted TypeScript:

```typescript
export type UUIDv7 = string & { readonly __brand: "UUIDv7" };

export function isUUIDv7(s: string): s is UUIDv7 { ... }
export function asUUIDv7(s: string): UUIDv7 { ... }
```

Usage in your frontend:

```typescript
import { UUIDv7, asUUIDv7 } from "./types/uuid";

function getUser(id: UUIDv7): User { ... }

const raw: string = await api.createUser();
const id: UUIDv7  = asUUIDv7(raw);  // throws TypeError if invalid
getUser(id);                        // compiles
getUser(raw);                       // TypeError: string is not UUIDv7
```

---

### Benchmarking

#### `from pendulumium.bench import run, profile`

The bench subpackage provides two functions for measuring performance on your machine.

**`run(n=100_000, *, verbose=True) -> dict`**

Benchmark generation and decode speed over `n` IDs. Reports individual generation speed, batch generation speed, decode speed, and collision count.

```python
from pendulumium.bench import run

run(100_000)

#   pendulumium benchmark — 100,000 IDs
#
#   generation              45.32 ms      2,206,642 IDs/sec
#   batch generation        18.91 ms      5,288,471 IDs/sec
#   decode                  312.44 ms       320,068 IDs/sec
#   collisions              0
#   batch speedup           2.40x
```

**`profile(seconds=5.0, *, verbose=True) -> dict`**

Run the generator flat-out for a fixed duration and report sustained throughput, peak IDs per millisecond, and counter overflow events.

```python
from pendulumium.bench import profile

profile(5.0)

#   pendulumium profile — 5.0s run
#
#   duration                 5.003 s
#   total generated       11,012,847
#   avg IDs/sec            2,201,236
#   peak IDs/ms                  847
#   counter overflows              0
```

Both functions return a dict for programmatic use when `verbose=False`.

---

## Advanced usage

### Scoped generators

By default, all calls to `uuid7()` share a single class-level lock and counter. For distributed environments where you want multiple workers to use non-overlapping node IDs, instantiate `Pendulumium` directly with an explicit `node_id`.

```python
from pendulumium import Pendulumium

# explicit node ID — 16-bit value, 0 to 65535
gen = Pendulumium(node_id=0xAB12)
uid = gen.generate()

# each instance has its own isolated lock and counter
gen_a = Pendulumium(node_id=0x0001)
gen_b = Pendulumium(node_id=0x0002)

uid_a = gen_a.generate()
uid_b = gen_b.generate()
```

Scoped generators do not share state with the class-level `uuid7()` function, so they can run in parallel without contention.

---

### Clock rollback handling

By default, if the system clock moves backwards (NTP sync, VM clock drift, manual change), `uuid7()` raises `RuntimeError` to prevent out-of-order IDs from being silently issued.

For long-running services where a hard crash is unacceptable, register a callback instead. The generator will call your callback, then spin-wait until the clock recovers — IDs remain monotonic and your service keeps running.

```python
import logging
from pendulumium import Pendulumium

def on_rollback(last_ms: int, current_ms: int) -> None:
    logging.warning(
        f"Clock rollback detected: {last_ms}ms → {current_ms}ms "
        f"(delta: {last_ms - current_ms}ms). Waiting for recovery."
    )

Pendulumium.on_clock_rollback(on_rollback)
```

---

### Generator stats

Inspect the current state of the class-level generator at any time.

```python
from pendulumium import Pendulumium

stats = Pendulumium.stats()
# {
#   "last_ms":         1778854750473,  # timestamp of most recent ID
#   "counter":         3,              # current sequence value
#   "node_id":         42139,          # 16-bit node identifier
#   "total_generated": 1000000,        # IDs issued since import
#   "peak_per_ms":     847,            # highest counter ever reached
# }
```

`peak_per_ms` is useful for capacity planning — if it regularly approaches `16383` (the 14-bit ceiling), you are at risk of counter overflow spin-waits under peak load.

---

## Caveats

**Counter overflow** — the sequence counter is 14 bits, giving 16,384 unique slots per millisecond. If more than 16,383 IDs are generated in a single millisecond, the generator spin-waits (sleeping ~1 µs at a time) until the clock ticks to the next millisecond. This keeps IDs monotonic but introduces latency. Use `batch()` or `stream()` for high-volume generation to minimize lock contention.

**Clock rollback** — if the system clock moves backwards (NTP sync, VM migration, manual change), monotonicity is broken by default with a `RuntimeError`. Register `on_clock_rollback()` to handle this gracefully in production.

**Node ID collisions** — the node ID is derived from `SHA-256(PID:hostname)`, truncated to 16 bits. In containerized, Kubernetes, or serverless environments where many processes share the same hostname and PID namespace, collisions are possible. Use `Pendulumium(node_id=...)` to assign explicit, non-overlapping node IDs.

**Fork safety** — the node ID is cached at class load time. If a process forks after import (e.g. with `multiprocessing`), child processes inherit the cached node ID and may produce colliding IDs. Call `Pendulumium._node_id = _derive_node_id()` in the child process after forking.

**Backdated IDs** — `from_datetime()` and `from_unix_ms()` generate IDs with past timestamps. If mixed into a stream of real-time IDs, they will sort before the real-time IDs, which may break assumptions about insert order in your database. Use backdated IDs only for isolated data migrations or test fixtures.

---

## Running tests

```bash
# install dev dependencies
pip install -e ".[dev]"

# run all tests individually
python tests/test_generator.py
python tests/test_decoder.py
python tests/test_validator.py
python tests/test_compare.py
python tests/test_convert.py
python tests/test_batch.py
python tests/test_stream.py
python tests/test_time.py
python tests/test_pretty.py
python tests/test_collisions.py
python tests/test_gaps.py
python tests/test_sql.py
python tests/test_types.py
python tests/test_bench.py

# run the benchmark
python -c "from pendulumium.bench import run; run()"

# run the profiler
python -c "from pendulumium.bench import profile; profile(5.0)"
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Ahmed Mughram
