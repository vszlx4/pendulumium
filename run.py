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
K = 10_000_000
seed = 3701661588

PRNG = XORShift32(seed)
start = time.time()

for _ in range(K): PRNG.random()

t = (time.time() - start) / K
estimated_total = t * N

print(f"Estimated time: {estimated_total:.2f} seconds")
print(f"Estimated minutes: {estimated_total/60:.2f}")

seen_benchmark = set()
start = time.time()
for i in range(K):
  state = i
  if state in seen_benchmark:
    pass
  seen_benchmark.add(state)
set_op_time = (time.time() - start) / K
set_overhead_total = set_op_time * N
estimated_with_overhead = estimated_total + set_overhead_total

print(f"\nEstimated time with set overhead: {estimated_with_overhead:.2f} seconds")
print(f"Estimated minutes with overhead: {estimated_with_overhead/60:.2f}")
print(f"Estimated set overhead: {set_overhead_total:.2f} seconds")

PRNG = XORShift32(seed)
seen = set()

start = time.time()

for i in range(N):
  state = PRNG.state

  if state in seen:
    print(f"Duplicate at step {i}: {state}")
    break

  seen.add(state)
  PRNG.random()

actual_time = time.time() - start

print(f"\nActual time: {actual_time:.2f} seconds")
print(f"Actual minutes: {actual_time/60:.2f}")
print("exit")