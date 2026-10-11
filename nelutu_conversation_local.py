"""Ephemeral, per-session conversational context for Neluțu.

This module does not persist, log, export or forward conversations to Gemini.
The Streamlit caller must instantiate a separate buffer for each user session.
Never populate this buffer with school records, secrets or sensitive messages.
"""
from __future__ import annotations

from dataclasses import dataclass, field

MAX_TURNS = 4
MAX_MESSAGE_CHARS = 600


@dataclass
class LocalConversation:
    """Short in-memory context; intentionally no disk or remote integration."""

    _turns: list[tuple[str, str]] = field(default_factory=list, repr=False)

    def append(self, role: str, message: str) -> bool:
        from nelutu_gemini_optional import is_public_general_chat

        if role not in ("user", "model"):
            self.clear()
            return False
        if not isinstance(message, str) or not is_public_general_chat(message):
            self.clear()
            return False
        self._turns.append((role, message[:MAX_MESSAGE_CHARS]))
        del self._turns[:-MAX_TURNS]
        return True

    def snapshot(self) -> tuple[tuple[str, str], ...]:
        """Local display/context only. Do NOT pass to Gemini generate()."""
        return tuple(self._turns)

    def clear(self) -> None:
        self._turns.clear()

    def __repr__(self) -> str:
        return "LocalConversation(turn_count=%d)" % len(self._turns)
