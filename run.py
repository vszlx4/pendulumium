import time
import os
import hashlib
import secrets
import threading

"""
CONSIDERATIONS:

1. Counter overflow:
   Limited to 65,535 generations per millisecond; exceeding this resets
   the counter to 0.

2. Clock rollback:
   If the system clock moves backwards, timestamps may decrease and
   ordering guarantees can break (e.g. NTP sync, VM clock drift,
   manual clock changes).

3. Multiprocessing collisions:
   PID separation reduces collision risk, but collisions may still occur
   in containerized, distributed, Kubernetes, serverless, or PID-reuse
   environments.

4. Fork safety:
   If a process forks after initialization, the cached PID may become
   stale in child processes, potentially causing identifier conflicts.
"""

class Pendulumium: # uppercase "P" due to Python's PascalCase naming convention. :<
  last_timestamp = 0; counter = 0; _lock = threading.Lock()

  @classmethod
  def nanoTSID(cls, as_string = True, formatted = True):
    with cls._lock:
      current_timestamp = int(time.time() * 1000) & ((1 << 48) - 1)

      if current_timestamp == cls.last_timestamp: 
        cls.counter += 1
      else: 
        cls.counter = 0
        cls.last_timestamp = current_timestamp

      counter = cls.counter & 0xFFFF

    pid = int(hashlib.sha256(str(os.getpid()).encode()).hexdigest(), 16) & 0xFFFF
    entropy = secrets.randbits(48)

    uuid_int = ((current_timestamp << 80) | (pid << 64) | (counter << 48) | entropy)
    if not as_string: 
      return uuid_int
    
    uuid_hex = f"{uuid_int:032x}"
    return uuid_hex if not formatted else f"{uuid_hex[:12]}-{uuid_hex[12:16]}-{uuid_hex[16:20]}-{uuid_hex[20:]}"
  
Pendulumium.nanoTSID()