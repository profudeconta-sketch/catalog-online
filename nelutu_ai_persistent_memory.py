"""Optional encrypted persistent memory prototype; never touches school records.

Uses Fernet authenticated encryption. Storage backend is supplied by the caller,
so the portal cannot accidentally use the catalog repository as a database.
"""
from __future__ import annotations
import json
import re
from dataclasses import dataclass
from cryptography.fernet import Fernet, InvalidToken
from nelutu_ai_memory import NelutuMemory
from nelutu_ai_privacy import approved_external_question
from nelutu_ai_answer_guard import safe_memory_answer

MAX_CIPHERTEXT_BYTES = 256_000

class MemoryStoreError(Exception):
    pass

def _validate_scope(scope: str) -> str:
    if not isinstance(scope, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{16,128}", scope):
        raise MemoryStoreError("invalid_scope")
    return scope

@dataclass
class EncryptedMemoryStore:
    """Requires a private store with get/put/delete methods and a secret key."""
    backend: object
    key: bytes

    def __post_init__(self):
        self._cipher = Fernet(self.key)

    def load(self, scope: str) -> NelutuMemory:
        scope = _validate_scope(scope)
        encrypted = self.backend.get(scope)
        if encrypted is not None and not isinstance(encrypted, bytes):
            raise MemoryStoreError("invalid_ciphertext_type")
        if encrypted is None:
            return NelutuMemory()
        if len(encrypted) > MAX_CIPHERTEXT_BYTES:
            raise MemoryStoreError("ciphertext_too_large")
        try:
            data = json.loads(self._cipher.decrypt(encrypted).decode("utf-8"))
            if not isinstance(data, list) or len(data) > 60 or len(data) % 2:
                raise ValueError("invalid_memory")
            memory = NelutuMemory()
            for index in range(0, len(data), 2):
                user, assistant = data[index], data[index + 1]
                if not isinstance(user, dict) or not isinstance(assistant, dict):
                    raise ValueError("invalid_turn")
                if user.get("role") != "user" or assistant.get("role") != "assistant":
                    raise ValueError("invalid_role")
                if set(user) != {"role", "content"} or set(assistant) != {"role", "content"}:
                    raise ValueError("unexpected_fields")
                if not memory.add(user.get("content", ""), assistant.get("content", "")):
                    raise ValueError("invalid_content")
            return memory
        except (InvalidToken, ValueError, TypeError, UnicodeError, KeyError) as exc:
            raise MemoryStoreError("cannot_decrypt_or_validate") from exc

    def save(self, scope: str, memory: NelutuMemory, *, consent: bool) -> None:
        scope = _validate_scope(scope)
        if consent is not True:
            raise MemoryStoreError("consent_required")
        if not isinstance(memory, NelutuMemory):
            raise MemoryStoreError("invalid_memory")
        if len(memory.turns) > 60 or len(memory.turns) % 2:
            raise MemoryStoreError("invalid_length")
        for index in range(0, len(memory.turns), 2):
            user, assistant = memory.turns[index:index + 2]
            if not isinstance(user, dict) or not isinstance(assistant, dict):
                raise MemoryStoreError("invalid_turn")
            if user.get("role") != "user" or assistant.get("role") != "assistant":
                raise MemoryStoreError("invalid_role")
            if set(user) != {"role", "content"} or set(assistant) != {"role", "content"}:
                raise MemoryStoreError("unexpected_fields")
            if not approved_external_question(user.get("content", "")):
                raise MemoryStoreError("private_question")
            answer = assistant.get("content")
            if not safe_memory_answer(answer):
                raise MemoryStoreError("invalid_answer")
        payload = json.dumps(memory.recent_local(60), ensure_ascii=False).encode("utf-8")
        encrypted = self._cipher.encrypt(payload)
        if len(encrypted) > MAX_CIPHERTEXT_BYTES:
            raise MemoryStoreError("ciphertext_too_large")
        self.backend.put(scope, encrypted)

    def delete(self, scope: str) -> None:
        self.backend.delete(_validate_scope(scope))
