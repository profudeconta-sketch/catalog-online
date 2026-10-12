"""Isolated tests for conditional catalog synchronization; no real school data or network."""
import ast
import hashlib
import io
import json
import os
import tempfile
import types
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch


class Session(dict):
    pass


class FakeStreamlit:
    def __init__(self):
        self.session_state = Session()
        self.secrets = {"GITHUB_TOKEN": "fake"}
        self.errors = []

    def error(self, message):
        self.errors.append(message)


class Response:
    def __init__(self, body, etag='"version-1"'):
        self.status = 200
        self.headers = {"ETag": etag}
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return self.body


class ConditionalSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.cwd = os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.cwd)
        source = Path(self.cwd, "app_web_catalog.py").read_text(encoding="utf-8")
        node = next(n for n in ast.parse(source).body
                    if isinstance(n, ast.FunctionDef) and n.name == "sync_excel_from_private_repo")
        self.st = FakeStreamlit()
        self.env = {
            "st": self.st, "os": os, "hashlib": hashlib,
            "urllib": urllib, "json": json,
            "base64": __import__("base64"), "shutil": __import__("shutil"),
            "_validate_excel_catalog": lambda path: None,
        }
        exec(compile(ast.Module(body=[node], type_ignores=[]), "app_web_catalog.py", "exec"), self.env)
        self.sync = self.env["sync_excel_from_private_repo"]
        self.filename = "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

    def test_unchanged_remote_skips_replacement(self):
        import base64
        body = json.dumps({"content": base64.b64encode(b"workbook-v1").decode()}).encode()
        requests = []

        def fetch(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return Response(body)
            self.assertEqual(request.headers.get("If-none-match"), '"version-1"')
            raise urllib.error.HTTPError(request.full_url, 304, "Not Modified", {}, io.BytesIO())

        with patch.object(urllib.request, "urlopen", side_effect=fetch):
            self.assertTrue(self.sync())
            self.assertTrue(self.sync())
        self.assertEqual(Path(self.filename).read_bytes(), b"workbook-v1")
        self.assertEqual(len(requests), 2)
        self.assertFalse(self.st.errors)

    def test_changed_local_file_disables_conditional_request(self):
        import base64
        body = json.dumps({"content": base64.b64encode(b"remote-v1").decode()}).encode()
        requests = []

        def fetch(request, timeout):
            requests.append(request)
            self.assertIsNone(request.headers.get("If-none-match"))
            return Response(body)

        with patch.object(urllib.request, "urlopen", side_effect=fetch):
            self.assertTrue(self.sync())
            Path(self.filename).write_bytes(b"local-changed")
            self.assertTrue(self.sync())
        self.assertEqual(Path(self.filename).read_bytes(), b"remote-v1")

    def test_remote_change_replaces_previous_version(self):
        import base64
        first = json.dumps({"content": base64.b64encode(b"remote-v1").decode()}).encode()
        second = json.dumps({"content": base64.b64encode(b"remote-v2").decode()}).encode()
        requests = []

        def fetch(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return Response(first, '"version-1"')
            self.assertEqual(request.headers.get("If-none-match"), '"version-1"')
            return Response(second, '"version-2"')

        with patch.object(urllib.request, "urlopen", side_effect=fetch):
            self.assertTrue(self.sync())
            self.assertTrue(self.sync())
        self.assertEqual(Path(self.filename).read_bytes(), b"remote-v2")
        self.assertEqual(self.st.session_state["_catalog_etag"], '"version-2"')

    def test_unexpected_network_error_fails_closed(self):
        with patch.object(urllib.request, "urlopen", side_effect=OSError("offline")):
            self.assertFalse(self.sync())
        self.assertTrue(self.st.errors)


if __name__ == "__main__":
    unittest.main()
