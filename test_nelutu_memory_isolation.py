import unittest
from nelutu_local_memory_checks import check_memory

class MemoryTest(unittest.TestCase):
    def test_isolation_and_reset(self):
        self.assertTrue(check_memory())

if __name__ == '__main__':
    unittest.main()
