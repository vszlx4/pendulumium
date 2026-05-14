import time
import os, hashlib
import secrets

class Pendulumium(): # uppercase "P" due to Python's PascalCase naming convention.
  last_timestamp = 0; counter = 0

  @classmethod
  def generate(cls):

    current_timestamp = int(time.time() * 1000) & ((1 << 48) - 1)

    if current_timestamp == cls.last_timestamp: cls.counter += 1
    else: cls.counter = 0; cls.last_timestamp = current_timestamp

    counter = cls.counter & 0xFFFF

    pid = int(hashlib.sha256(str(os.getpid()).encode()).hexdigest(), 16) & 0xFFFF
    entropy = secrets.randbits(48)

    uuid_int = ((current_timestamp << 80) | (pid << 64) | (counter << 48) | entropy)
    uuid_hex = f"{uuid_int:032x}"
    formatted = f"{uuid_hex[:12]}-{uuid_hex[12:16]}-{uuid_hex[16:20]}-{uuid_hex[20:]}"

    return uuid_int.to_bytes(16, "big"), uuid_hex, formatted


seen = set()

for i in range(10_000_000):
  z, x, x = Pendulumium.generate()
  seen.add(z)

print(f"{len(seen):,.2f}")