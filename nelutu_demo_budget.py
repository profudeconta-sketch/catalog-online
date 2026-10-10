"""Offline, per-session request budget for the isolated Neluțu demo.

Not a server-wide quota or a substitute for provider-side restrictions.
"""
from dataclasses import dataclass

MAX_DEMO_CALLS = 3

@dataclass
class DemoBudget:
    used: int = 0

    def allowed(self) -> bool:
        return self.used < MAX_DEMO_CALLS

    def consume(self) -> bool:
        if not self.allowed():
            return False
        self.used += 1
        return True

    def remaining(self) -> int:
        return max(0, MAX_DEMO_CALLS - self.used)

    def reset(self) -> None:
        self.used = 0
