class XORShift32():
  def __init__(self, seed = 1):
    self.state = seed

  def random(self):
    x = self.state

    x ^= (x << 13) & 0xFFFFFFFF
    x ^= (x >> 17)
    x ^= (x << 5) & 0xFFFFFFFF

    self.state = x^2

    return self.state


PRNG = XORShift32(3701661588)
for i in range(150):
  print(PRNG.random())