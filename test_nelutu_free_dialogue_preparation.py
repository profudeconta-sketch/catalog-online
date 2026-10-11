"""Offline tests for Neluțu free-dialogue preparation."""
import unittest
from nelutu_free_dialogue_preparation import prepare_public_dialogue


class DialogueTests(unittest.TestCase):
    def test_simple_dialogue(self):
        result = prepare_public_dialogue(
            (("user", "Salut!"), ("model", "Salut, cu ce te ajut?")),
            "Povesteste-mi despre stele.", consent=True,
        )
        self.assertEqual([x["role"] for x in result], ["user", "model", "user"])

    def test_consent_required(self):
        self.assertIsNone(prepare_public_dialogue((), "Salut!"))

    def test_school_data_blocked(self):
        self.assertIsNone(prepare_public_dialogue((), "Ce nota are elevul?", consent=True))
        self.assertIsNone(prepare_public_dialogue(
            (("user", "Ce nota are elevul?"), ("model", "Nu stiu.")),
            "Salut!", consent=True,
        ))

    def test_history_must_alternate(self):
        self.assertIsNone(prepare_public_dialogue(
            (("user", "Salut!"), ("user", "Buna!")), "Ce faci?", consent=True,
        ))

    def test_malformed_history(self):
        self.assertIsNone(prepare_public_dialogue([("user", "Salut!")], "Salut!", consent=True))
        self.assertIsNone(prepare_public_dialogue((("user", "Salut!"),), "Salut!", consent=True))

    def test_bounded(self):
        history = tuple(("user" if i % 2 == 0 else "model", "Salut!") for i in range(8))
        self.assertIsNone(prepare_public_dialogue(history, "Salut!", consent=True))


if __name__ == "__main__":
    unittest.main()
