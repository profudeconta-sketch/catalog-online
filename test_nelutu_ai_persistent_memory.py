import unittest
from cryptography.fernet import Fernet
from nelutu_ai_memory import NelutuMemory
from nelutu_ai_persistent_memory import EncryptedMemoryStore, MemoryStoreError

class PrivateBackend:
    def __init__(self): self.items = {}
    def get(self, key): return self.items.get(key)
    def put(self, key, value): self.items[key] = value
    def delete(self, key): self.items.pop(key, None)

class EncryptedMemoryTests(unittest.TestCase):
    def setUp(self):
        self.backend = PrivateBackend()
        self.store = EncryptedMemoryStore(self.backend, Fernet.generate_key())
        self.scope_a = "parent_session_123456"
        self.scope_b = "parent_session_987654"

    def test_encrypted_roundtrip(self):
        memory = NelutuMemory()
        memory.add("De ce învățăm matematica?", "Pentru gândire.")
        self.store.save(self.scope_a, memory, consent=True)
        self.assertNotIn("matematica", self.backend.items[self.scope_a].decode())
        self.assertEqual(self.store.load(self.scope_a).size(), 1)
        self.assertEqual(self.store.load(self.scope_b).size(), 0)

    def test_consent_required(self):
        with self.assertRaises(MemoryStoreError):
            self.store.save(self.scope_a, NelutuMemory(), consent=False)
        self.assertEqual(self.backend.items, {})

    def test_delete(self):
        self.store.save(self.scope_a, NelutuMemory(), consent=True)
        self.store.delete(self.scope_a)
        self.assertEqual(self.store.load(self.scope_a).size(), 0)

    def test_wrong_key_fails_closed(self):
        self.store.save(self.scope_a, NelutuMemory(), consent=True)
        other = EncryptedMemoryStore(self.backend, Fernet.generate_key())
        with self.assertRaises(MemoryStoreError):
            other.load(self.scope_a)

    def test_scope_validation(self):
        with self.assertRaises(MemoryStoreError):
            self.store.load("../school_catalog")

if __name__ == "__main__":
    unittest.main()
