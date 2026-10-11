"""Process-local shared test budget; NOT a provider-wide or durable quota."""
from __future__ import annotations

from threading import Lock

MAX_INSTANCE_ATTEMPTS = 12


class InstanceBudget:
    """Thread-safe, non-resettable within one running instance."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._used = 0

    def remaining(self) -> int:
        with self._lock:
            return max(0, MAX_INSTANCE_ATTEMPTS - self._used)

    def allowed(self) -> bool:
        return self.remaining() > 0

    def consume(self) -> bool:
        with self._lock:
            if self._used >= MAX_INSTANCE_ATTEMPTS:
                return False
            self._used += 1
            return True


class SharedBudgetGate:
    """Reserve session and instance quotas together, never refund provider attempts.

    This is only a process-local test gate; it does not survive restarts.
    """

    def __init__(self, instance: InstanceBudget) -> None:
        self.instance = instance
        self._lock = Lock()

    def reserve(self, session_budget) -> bool:
        with self._lock:
            if not session_budget.allowed():
                return False
            if not self.instance.consume():
                return False
            return session_budget.consume()
