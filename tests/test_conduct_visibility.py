"""Teste izolate: note purtare afișate doar din registru valid, fără date reale."""
import base64
import datetime
import json
import unittest
from unittest.mock import patch

from annual_closure_engine import CLJ_2026_2027_COURSE_INTERVALS
from conduct_view import (
    CONDUCT_ANNUAL_NOTICE,
    ConductViewError,
    conduct_interval_rows,
    fetch_private_conduct_registry,
)


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


def sample_registry():
    return {
        "schema_version": 1,
        "school_year": "2026-2027",
        "grades": [
            {
                "student_key": "RM-1",
                "interval_number": 1,
                "grade": 9,
                "awarded_on": CLJ_2026_2027_COURSE_INTERVALS[0].end_date.isoformat(),
            },
            {
                "student_key": "RM-2",
                "interval_number": 1,
                "grade": 5,
                "awarded_on": CLJ_2026_2027_COURSE_INTERVALS[0].end_date.isoformat(),
            },
        ],
    }


class ConductVisibilityTests(unittest.TestCase):
    def test_own_grades_only_and_all_five_rows(self):
        rows = conduct_interval_rows(sample_registry(), "RM-1")
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]["Nota la purtare"], "9")
        self.assertEqual(rows[1]["Nota la purtare"], "Neacordată")
        self.assertNotIn("5", [r["Nota la purtare"] for r in rows])

    def test_no_grades_are_not_guessed_from_absences(self):
        registry = sample_registry()
        registry["grades"] = []
        rows = conduct_interval_rows(registry, "RM-1")
        self.assertTrue(all(row["Nota la purtare"] == "Neacordată" for row in rows))

    def test_duplicate_grade_blocks_display(self):
        registry = sample_registry()
        registry["grades"].append(dict(registry["grades"][0]))
        with self.assertRaises(ConductViewError):
            conduct_interval_rows(registry, "RM-1")

    def test_invalid_grade_or_future_interval_blocks_display(self):
        registry = sample_registry()
        registry["grades"][0]["grade"] = 11
        with self.assertRaises(ConductViewError):
            conduct_interval_rows(registry, "RM-1")
        registry["grades"][0]["grade"] = 9
        registry["grades"][0]["awarded_on"] = "2026-09-01"
        with self.assertRaises(ConductViewError):
            conduct_interval_rows(registry, "RM-1")

    def test_missing_token_blocks_remote_read(self):
        with self.assertRaises(ConductViewError):
            fetch_private_conduct_registry("")

    def test_remote_read_only_and_no_stale_fallback(self):
        record_bytes = json.dumps(sample_registry()).encode("utf-8")
        payload = json.dumps({"content": base64.b64encode(record_bytes).decode("ascii")}).encode()
        requests = []
        def fake_open(req, timeout):
            requests.append((req, timeout))
            return FakeResponse(payload)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            actual = fetch_private_conduct_registry("test-token")
        self.assertEqual(actual["grades"][0]["grade"], 9)
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0][0].get_method(), "GET")
        self.assertIn("registru_purtare", requests[0][0].full_url)
        with patch("urllib.request.urlopen", side_effect=OSError("offline")):
            with self.assertRaises(ConductViewError):
                fetch_private_conduct_registry("test-token")

    def test_notice_mentions_both_legal_thresholds_and_annual_only(self):
        self.assertIn("20 de absențe", CONDUCT_ANNUAL_NOTICE)
        self.assertIn("20% absențe", CONDUCT_ANNUAL_NOTICE)
        self.assertIn("sfârșitul anului", CONDUCT_ANNUAL_NOTICE)
        self.assertIn("media anuală la purtare", CONDUCT_ANNUAL_NOTICE)


if __name__ == "__main__":
    unittest.main()
