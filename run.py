import time

class XORShift32():
  def __init__(self, seed = 1):
    self.state = seed

  def random(self):
    x = self.state

    x ^= (x << 13) & 0xFFFFFFFF
    x ^= (x >> 17)
    x ^= (x << 5) & 0xFFFFFFFF

    self.state = x

    return self.state

N = 100_000_000
K = 1_000_000
seed = 3701661588

PRNG = XORShift32(seed)
start = time.time()

for _ in range(K): PRNG.random()

t = (time.time() - start) / K
estimated_total = t * N

print(f"Estimated time: {estimated_total:.2f} seconds")
print(f"Estimated minutes: {estimated_total/60:.2f}")

seen = set()

for i in range(N):
  state = PRNG.state

  if state in seen:
    print(f"Duplicate at step {i}: {state}")
    break

  seen.add(state)
  PRNG.random()

print("exit")