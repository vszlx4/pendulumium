"""
bench/runner.py - benchmarking and profiling for pendulumium.

  run(n)           - benchmark generation and decode speed over n IDs
  profile(seconds) - profile throughput over a fixed time duration
"""

from __future__ import annotations

import time as _time
import statistics

from ..core.generator import Pendulumium
from ..core.batch import batch
from ..inspection.decoder import decode
from ..inspection.collisions import check_collisions
from typing import cast


def run(n: int = 100_000, *, verbose: bool = True) -> dict[str, object]:
  """
  Benchmark generation and decode speed over *n* IDs.

  Measures:
    - Total generation time and IDs/second
    - batch() vs individual uuid7() speed comparison
    - Decode speed (IDs/second through decode())
    - Collision check across all generated IDs

  Args:
    n:       number of IDs to generate (default 100_000)
    verbose: if True (default), prints a formatted report to stdout.

  Returns:
    A dict with keys:
      n                 - number of IDs tested
      gen_time_ms       - total generation time in milliseconds
      gen_per_second    - IDs generated per second
      batch_time_ms     - batch() generation time in milliseconds
      batch_per_second  - batch() IDs per second
      decode_time_ms    - total decode time in milliseconds
      decode_per_second - IDs decoded per second
      collisions        - number of collisions found (should be 0)

  Raises:
    ValueError - if n < 1.

  Example:
    >>> from pendulumium.bench import run
    >>> run(50_000)
  """
  if n < 1:
    raise ValueError(f"n must be >= 1, got {n}.")
  
  gen_start      = _time.perf_counter()
  ids            = [Pendulumium.uuid7() for _ in range(n)]
  gen_end        = _time.perf_counter()
  gen_time_ms    = (gen_end - gen_start) * 1_000
  gen_per_second = int(n / (gen_end - gen_start))

  batch_start      = _time.perf_counter()
  batch_ids        = batch(n)
  batch_end        = _time.perf_counter()
  batch_time_ms    = (batch_end - batch_start) * 1_000
  batch_per_second = int(n / (batch_end - batch_start))

  sample    = [str(i) for i in ids[:min(n, 10_000)]]
  dec_start = _time.perf_counter()
  for uid in sample:
    decode(uid)
  dec_end           = _time.perf_counter()
  dec_elapsed       = dec_end - dec_start
  decode_time_ms    = dec_elapsed * 1_000
  decode_per_second = int(len(sample) / dec_elapsed)

  collision_result = check_collisions([str(i) for i in ids])
  collisions       = cast(int, collision_result["collisions"])

  result: dict[str, object] = {
    "n":                 n,
    "gen_time_ms":       round(gen_time_ms, 2),
    "gen_per_second":    gen_per_second,
    "batch_time_ms":     round(batch_time_ms, 2),
    "batch_per_second":  batch_per_second,
    "decode_time_ms":    round(decode_time_ms, 2),
    "decode_per_second": decode_per_second,
    "collisions":        collisions,
  }

  if verbose:
    print(f"\n  pendulumium benchmark — {n:,} IDs\n")
    print(f"  {'generation':<24} {gen_time_ms:>10.2f} ms   {gen_per_second:>12,} IDs/sec")
    print(f"  {'batch generation':<24} {batch_time_ms:>10.2f} ms   {batch_per_second:>12,} IDs/sec")
    print(f"  {'decode':<24} {decode_time_ms:>10.2f} ms   {decode_per_second:>12,} IDs/sec")
    print(f"  {'collisions':<24} {collisions:>10}")
    print(f"  {'batch speedup':<24} {batch_per_second / gen_per_second:>10.2f}x")
    print()

  return result


def profile(seconds: float = 5.0, *, verbose: bool = True) -> dict[str, object]:
  """
  Profile throughput by running the generator flat-out for *seconds*.

  Unlike run(), which tests a fixed number of IDs, profile() runs for
  a fixed duration and measures what actually happened — useful for 
  detecting counter overflow prssure and sustained throughput.

  Args:
    seconds: how long to run in seconds (default 5.0).
    verbose: if True (default), prints a formatted report to stdout.

  Returns:
    A dict with keys:
      duration_s      - actual measured duration in seconds
      total_generated - total IDs generated
      avg_per_second  - average IDs per second
      peak_per_ms     - highest IDs generated in a single millisecond
      overflows       - counter overflow events (spin-waits triggered)

  Raises:
    ValueError - if seconds < 0.1.

  Example:
    >>> from pendulumium.bench import profile
    >>> profile(3.0)
  """
  if seconds < 0.1:
    raise ValueError(f"seconds must be >= 0.1, got {seconds}.")
  
  # reset peak counter so we get a clean reading for this run
  with Pendulumium._lock:
    Pendulumium._peak_per_ms = 0
    before_total             = Pendulumium._total_generated
  
  per_ms_counts: list[int] = []
  overflows                = 0
  last_ms                  = Pendulumium._last_ms

  deadline = _time.perf_counter() + seconds
  start    = _time.perf_counter()

  while _time.perf_counter() < deadline:
    Pendulumium.uuid7()

    current_ms = Pendulumium._last_ms
    if current_ms != last_ms:
      count = Pendulumium._counter
      per_ms_counts.append(count)
      if count >= 0x3FFF:
        overflows += 1
      last_ms = current_ms

  end      = _time.perf_counter()
  duration = end - start

  with Pendulumium._lock:
    total = Pendulumium._total_generated - before_total
    peak  = Pendulumium._peak_per_ms

  avg_per_second = int(total / duration)

  result: dict[str, object] = {
    "duration_s":      round(duration, 3),
    "total_generated": total,
    "avg_per_second":  avg_per_second,
    "peak_per_ms":     peak,
    "overflows":       overflows
  }

  if verbose:
    print(f"\n  pendulumium profile — {seconds:.1f}s run\n")
    print(f"  {'duration':<24} {duration:>10.3f} s")
    print(f"  {'total generated':<24} {total:>10,}")
    print(f"  {'avg IDs/sec':<24} {avg_per_second:>10,}")
    print(f"  {'peak IDs/ms':<24} {peak:>10,}")
    print(f"  {'counter overflows':<24} {overflows:>10}")
    print()

  return result
