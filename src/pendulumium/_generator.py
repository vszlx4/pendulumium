import time
import os
import socket
import hashlib
import secrets
import threading

"""
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


class Pendulumium:
  _lock    = threading.Lock()
  _last_ms = 0
  _last_ns = 0
  _counter = 0

  _node_id: int = (
    int(
      hashlib.sha256(
        f"{os.getpid()}:{socket.gethostname()}".encode()
      ).hexdigest(), 16
      ) & 0xFFFF
  )

  @classmethod
  def _now_ns(cls) -> tuple[int, int]:
    """Return unix_ms, nanosecond_remainder_within_that_ms"""
    ns_total = time.time_ns()
    ms = ns_total // 1_000_000
    ns_rem = ns_total % 1_000_000
    return ms, ns_rem

  @classmethod
  def p0111(cls, as_string: bool = True, formatted: bool = True) -> "int | str":
    with cls._lock:
      ms, ns_rem = cls._now_ns()

      if ms == cls._last_ms:
        cls._counter += 1
        if cls._counter > 0x3FFF:
          while True:
            ms, ns_rem = cls._now_ns()
            if ms != cls._last_ms: 
              break
            time.sleep(1e-6) #yield ~1 µs, "microsecond"
          cls._counter = 0
          cls._last_ms = ms
          cls._last_ns = ns_rem
      else:
        if ms < cls._last_ms:
          raise RuntimeError(f"[!] Clock moved backwards: last={cls._last_ms} now={ms}")
        cls._counter = 0
        cls._last_ms = ms
        cls._last_ns = ns_rem

      ts      = ms & ((1 << 48) - 1)
      sub_ms  = (ns_rem * 0xFFF) // 999_999 #scale NS remainder to 12 bits
      seq     = cls._counter & 0x3FFF
      node    = cls._node_id
      entropy = secrets.randbits(32)

      # >>> assemble 128bits
      # [127:80] timestamp (48 bits)
      # [79:76]  version 7 ( 4 bits, 0b0111)
      # [75:64]  sub-ms    (12 bits)
      # [63:62]  variant   ( 2 bits, 0b10)
      # [61:48]  sequence  (14 bits)
      # [47:32]  node      (16 bits)
      # [31:0]   entropy   (32 bits)

      uuid_int = (
          (ts     << 80)
        | (0x7    << 76)
        | (sub_ms << 64)
        | (0b10   << 62)
        | (seq    << 48)
        | (node   << 32)
        | (entropy)
      ) & ((1     << 128) - 1) #clamp

      if not as_string: return uuid_int
      h = f"{uuid_int:032x}"
      return h if not formatted else f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"