"""
core/generator.py - UUID v7 generator.

LAYOUT (128 bits - UUID v7 compliant):

  [127:80]  48 bits  Unix timestamp in milliseconds
  [79:76]    4 bits  Version = 0b0111 (UUID v7)
  [75:64]   12 bits  Sub-millisecond nanosecond remainder (0-999_999), scaled to 12 bits
  [63:62]    2 bits  Variant = 0b10 (RFC 9562 required)
  [61:48]   14 bits  Monotonic sequence counter (resets per millisecond)
  [47:32]   16 bits  Node ID: SHA-256(PID + hostname), truncated
  [31:0]    32 bits  Cryptographic entropy

Collision resistance:
  - Same-ms, same-node: sequence gives 16_384 unique slots before entropy matters
  - Cross-node: 16-bit node ID separates instances
  - Worst-case: ~2^46 probabilistic uniqueness from sequence + node + entropy combined

Caveats:
  1. Counter overflow: >16_383 IDs/ms spins until the next millisecond.
  2. Clock rollback: monotonicity breaks on NTP sync or manual clock changes.
  3. Node ID collisions: PID+hostname hash may collide in containerized/k8s environments.
  4. Fork safety: node ID is cached at class load; child processes must reinitialize.
"""

import time
import os
import socket
import hashlib
import secrets
import threading

from collections.abc import Callable


def _derive_node_id() -> int:
  """Derive a 16-bit node ID from the current PID and hostname."""
  return (
    int(
      hashlib.sha256(
        f"{os.getpid()}:{socket.gethostname()}".encode()
      ).hexdigest(),
      16,
    )
    & 0xFFFF
  )


class Pendulumium:
  """
  UUID v7 generator.

  Class-level usage (shared state, recommended for most cases):
    from pendulumium import uuid7
    uid = uuid7()

  Scoped usage (explict node ID, for distributed environments):
    gen = Pendulumium(node_id=0xAB12)
    uid = gen.generate()
  """

  _lock:              threading.Lock = threading.Lock()
  _last_ms:           int            = 0
  _last_ns:           int            = 0
  _counter:           int            = 0
  _total_generated:   int            = 0
  _peak_per_ms:       int            = 0
  _node_id:           int            = _derive_node_id()
  _rollback_callback: Callable[[int, int], None] | None = None


  def __init__(self, node_id: int | None = None) -> None:
    """
    Create a scoped generator instance with an optional explicit node ID.

    Args:
      node_id: a 16-bit integer (0-65535) to use as the node identifier.
               If None, derives the node ID from PID + hostname as usual.

    Raises:
      ValueError - if node_id is out of 16-bit range.

    Example:
      >>> gen = Pendulumium(node_id=0xAB12)
      >>> uid = gen.generate()
    """
    if node_id is not None:
      if not (0 <= node_id <= 0xFFFF):
        raise ValueError(
          f"node_id must be in range 0-65535, got {node_id}."
        )
      self._instance_node_id: int | None = node_id
    else:
      self._instance_node_id = None

    self._instance_lock:    threading.Lock = threading.Lock()
    self._instance_last_ms: int            = 0
    self._instance_last_ns: int            = 0
    self._instance_counter: int            = 0

  
  @staticmethod
  def _now_ns() -> tuple[int, int]:
    """Return (unix_ms, nanosecond_remainder_within_that_ms)."""
    ns_total = time.time_ns()
    ms       = ns_total // 1_000_000
    ns_rem   = ns_total % 1_000_000
    return ms, ns_rem
  

  @classmethod
  def on_clock_rollback(cls, callback: Callable[[int, int], None]) -> None:
    """
    Register a callback invoked on clock rollback instead of raising.

    By default, a clock rollback raises RuntimeError. Registering a
    callback overrides that — the callback is called with (last_ms,
    current_ms) and the generator spin-waits until the clock recovers,
    keeping IDs monotonic without crashing.

    Useful for long-running services where a hard crash on NTP sync
    is unacceptable.

    Args:
      callback: callable(last_ms: int, current_ms: int) -> None.

    Example:
      >>> import logging
      >>> Pendulumium.on_clock_rollback(
      ...   lambda last, now: logging.warning(f"Clock rollback: {last} -> {now}")
      ... )
    """
    cls._rollback_callback = callback


  @classmethod
  def stats(cls) -> dict[str, int]:
    """
    Return a snapshot of the class-level generator state.

    Keys:
      last_ms         - timestamp of the most recently issued ID (Unix ms)
      counter         - current sequence value within that millisecond
      node_id         - 16-bit node identifier
      total_generated - cumulative IDs isued since import
      peak_per_ms     - highest counter value ever reached in a single ms

    Example:
      >>> Pendulumium.stats()
      {'last_ms': 1748475060489, 'counter': 3, 'node_id': 42139, ...}
    """
    with cls._lock:
      return {
        "last_ms":         cls._last_ms,
        "counter":         cls._counter,
        "node_id":         cls._node_id,
        "total_generated": cls._total_generated,
        "peak_per_ms":     cls._peak_per_ms,
      }
    
  
  @staticmethod
  def _build(ms: int, ns_rem: int, seq: int, node: int) -> int:
    """Assemble a 128-bit UUID v7 integer from its constituent fields."""
    ts     = ms & ((1 << 48) - 1)
    sub_ms = (ns_rem * 0xFFF) // 999_999

    return (
      (ts     << 80)
      | (0x7    << 76)
      | (sub_ms << 64)
      | (0b10   << 62)
      | (seq    << 48)
      | (node   << 32)
      | secrets.randbits(32)
    ) & ((1 << 128) - 1)
  

  @staticmethod
  def _format(uuid_int: int, as_string: bool, formatted: bool) -> int | str:
    """Format a 128-bit integer as a UUID string or return it as-is."""
    if not as_string:
      return uuid_int
    h = f"{uuid_int:032x}"
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}" if formatted else h
  

  @classmethod
  def uuid7(cls, as_string: bool = True, formatted: bool = True) -> int | str:
    """
    Generate a single UUID v7 using shared class-level state.

    Args:
      as_string: if True (default), returns a hex string.
                 if False, returns a 128-bit integer.
      formatted: if True (default), inserts RFC hyphens (8-4-4-4-12).
                 ignored when as_string is False.

    Raises:
      RuntimeError - on clock rollback (unless on_clock_rollback() is set).
    
    Example:
      >>> uuid7()
      "019e2c01-6909-7583-800a-8afe60572a94"
    """
    with cls._lock:
      ms, ns_rem = cls._now_ns()

      if ms < cls._last_ms:
        if cls._rollback_callback is not None:
          cls._rollback_callback(cls._last_ms, ms)
          while ms < cls._last_ms:
            ms, ns_rem = cls._now_ns()
        else:
          raise RuntimeError(
            f"[!] Clock moved backwards: last={cls._last_ms} now={ms}"
          )
        
      if ms == cls._last_ms:
        cls._counter += 1
        if cls._counter > 0x3FFF:
          while ms == cls._last_ms:
            ms, ns_rem = cls._now_ns()
            time.sleep(1e-6)
          cls._counter = 0
      else:
        cls._counter = 0
      
      cls._last_ms = ms
      cls._last_ns = ns_rem
      cls._total_generated += 1
      cls._peak_per_ms = max(cls._peak_per_ms, cls._counter)

      uuid_int = cls._build(ms, ns_rem, cls._counter, cls._node_id)
    
    return cls._format(uuid_int, as_string, formatted)

  
  def generate(self, as_string: bool = True, formatted: bool = True) -> int | str:
    """
    Generate a single UUID v7 using this instance's isolated state.

    Identical behavior to uuid7() but uses a separate lock and counter,
    so mulitple Pendulumium instances don't share sequence state.

    Args:
      as_string: if True (default), returns a hex string.
                 if False, returns a 128-bit integer.
      formatted: if True (default), inserts RFC hyphens (8-4-4-4-12).

    Example:
      >>> gen = Pendulumium(node_id=0xAB12)
      >>> gen.generate()
      "019e2c01-6909-7ab1-800a-8afe60572a94"
    """
    node = self._instance_node_id if self._instance_node_id is not None \
           else _derive_node_id()
    
    with self._instance_lock:
      ms, ns_rem = self._now_ns()

      if ms == self._instance_last_ms:
        self._instance_counter += 1
        if self._instance_counter > 0x3FFF:
          while ms == self._instance_last_ms:
            ms, ns_rem = self._now_ns()
            time.sleep(1e-6)
          self._instance_counter = 0
      else:
        self._instance_counter = 0
      
      self._instance_last_ms = ms
      self._instance_last_ns = ns_rem

      uuid_int = self._build(ms, ns_rem, self._instance_counter, node)

    return self._format(uuid_int, as_string, formatted)
