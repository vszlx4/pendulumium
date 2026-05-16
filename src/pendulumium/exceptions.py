"""Custom exceptions for pendulumium"""

class PendulumiumError(Exception):
  """Base exception for all pendulumium errors."""


class ClockRollbackError(PendulumiumError):
  """Raised when the system clock moves backwards."""

  def __init__(self, last_ms: int, current_ms: int) -> None:
    self.last_ms    = last_ms
    self.current_ms = current_ms
    super().__init__(
      f"Clock moved backwards: last={last_ms}ms, now={current_ms}ms "
      f"(delta={last_ms - current_ms}ms). "
      "Check for NTP sync, VM clock drift, or manual clock changes."
    )


class InvalidUUIDError(PendulumiumError):
  """Raised when a string is not a valid UUID v7."""

  def __init__(self, value: str, reason: str = "") -> None:
    self.value = value
    msg = f"Invalid UUID v7: {value!r}"
    if reason:
      msg += f" - {reason}"
    super().__init__(msg)