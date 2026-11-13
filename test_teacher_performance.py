"""Regresii pentru randarea la cerere și reconcilierea sigură a Inboxului.

Nu importă aplicația Streamlit și nu citește registre reale cu date personale.
"""
import ast
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import notification_storage as ns


class TeacherLazyUIContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Path("app_web_catalog.py").read_text(encoding="utf-8")

    def test_teacher_app_remains_valid_python(self):
        ast.parse(self.source)

    def test_all_existing_catalog_tabs_are_gated_by_active_state(self):
        s = self.source
        self.assertIn('key="catalog_active_section", on_change="rerun"', s)
        for tab in ("tab1", "tab2", "tab3", "tab_del", "tab4", "tab5",
                    "tab6", "tab7", "tab8", "tab9", "tab_photo"):
            self.assertIn(f"if {tab}.open:", s)
            self.assertIn(f"with {tab}:", s)

    def test_refresh_does_not_log_out_or_modify_primary_records(self):
        s = self.source
        start = s.index("def _refresh_teacher_view():")
        end = s.index("# --- GENERATOARE PDF ---", start)
        block = s[start:end]
        self.assertIn('st.session_state.pop(key, None)', block)
        self.assertIn("st.rerun()", block)
        self.assertNotIn('["authenticated"] = False', block)
        self.assertNotIn("private_write(", block)
        self.assertNotIn("push_to_github(", block)
        self.assertIn("🔄 Actualizează fișa elevului", s)
        self.assertIn("🔄 Actualizează documentele elevului", s)

    def test_inbox_actions_are_bound_to_current_source_and_revision(self):
        s = self.source
        begin = s.index("# Inbox global diriginte")
        end = s.index("tab1, tab2, tab3", begin)
        block = s[begin:end]
        self.assertIn("if _inbox_panel.open:", block)
        self.assertIn('str(item.get("revision",1))==str(_n.get("source_revision") or 1)', block)
        self.assertIn('if _leave.get("status") == LEAVE_STATUS_PENDING:', block)
        self.assertIn("approve_leave_request(", block)
        self.assertIn("refuse_leave_request(", block)
        self.assertIn("expected_revision=_leave[\"revision\"]", block)
        self.assertIn("read_approved_leave_pass(_leave_rm_pg,_source_id)", block)
        self.assertIn("student_rm_pg=_leave_rm_pg", block)
        self.assertNotIn("student_rm_pg=_student_key", block)
        self.assertNotIn("read_approved_leave_pass(_student_key,_source_id)", block)
        self.assertIn("_student_rm_pg_by_key.get(_student_key)", block)
        self.assertIn('st.session_state.pop("_teacher_inbox_cache", None)', block)

    def test_document_panels_are_opened_explicitly(self):
        s = self.source
        for panel in ("doc_leave_panel", "doc_sent_panel", "doc_received_panel"):
            self.assertIn(f"if _{panel}.open:", s)
            self.assertIn(f'key="{panel}", on_change="rerun"', s)


class ApprovedLeaveIdentityTests(unittest.TestCase):
    def test_approved_pdf_read_uses_original_rm_pg_exactly_once(self):
        """Read-only regression: hashed keys must not be re-hashed."""
        import hashlib
        import leave_pass_storage as leave
        from document_storage import normalize_student_key

        original_rm_pg = "126/TEST"
        key = normalize_student_key(original_rm_pg)
        request_id = "1234567890abcdef1234567890abcdef"
        pdf = b"%PDF-1.4\\nDummy test document"
        registry = {"schema_version": 1, "requests": [{
            "id": request_id, "student_key": key, "status": leave.STATUS_APPROVED,
            "document_path": "documente_scolare/test/approved.pdf",
            "document_sha256": hashlib.sha256(pdf).hexdigest(),
        }]}
        with patch.object(leave, "load_leave_pass_registry", return_value=(registry, "sha")), \\
             patch.object(leave, "private_read", return_value=(pdf, "sha")):
            record, content = leave.read_approved_leave_pass(original_rm_pg, request_id)
            self.assertEqual(record["student_key"], key)
            self.assertEqual(content, pdf)
            with self.assertRaises(leave.DocumentStorageError):
                leave.read_approved_leave_pass(key, request_id)


class TeacherReconciliationBatchTests(unittest.TestCase):
    def setUp(self):
        self.registry = {"schema_version": 1, "events": []}
        self.version = 0
        self.reads = 0
        self.writes = 0
        self.conflict_once = False

    def read(self, path):
        self.reads += 1
        return json.dumps(self.registry).encode("utf-8"), "sha-" + str(self.version)

    def write(self, path, raw, expected_sha, message):
        self.writes += 1
        if self.conflict_once:
            self.conflict_once = False
            raise ns.DocumentConflictError("Simulated concurrent write")
        if expected_sha != "sha-" + str(self.version):
            raise ns.DocumentConflictError("Unexpected version")
        self.registry = json.loads(raw.decode("utf-8"))
        self.version += 1
        return "sha-" + str(self.version)

    def sources(self):
        docs = {"schema_version": 1, "documents": [
            {"id": f"doc-{i}", "direction": "PARINTE_SCOALA", "student_key": "S1",
             "created_at_utc": "2026-11-13T08:00:00+00:00"}
            for i in range(25)
        ]}
        docs["documents"].append({"id": "school-doc", "direction": "SCOALA_PARINTE",
                                   "student_key": "S1"})
        leaves = {"schema_version": 1, "requests": [
            {"id": f"leave-{i}", "student_key": "S1", "revision": 1,
             "transmitted_at_utc": "2026-11-13T08:00:00+00:00"}
            for i in range(5)
        ]}
        return docs, leaves

    def test_many_sources_need_only_one_notification_write(self):
        docs, leaves = self.sources()
        with patch.object(ns, "private_read", self.read), \
             patch.object(ns, "private_write", self.write), \
             patch.object(ns, "load_registry", return_value=(docs, None)), \
             patch.object(ns, "load_leave_pass_registry", return_value=(leaves, None)):
            self.assertEqual(ns.reconcile_teacher_inbox(), 30)
            self.assertEqual(self.writes, 1)
            self.assertEqual(self.reads, 1)
            self.assertEqual(len(self.registry["events"]), 30)
            self.assertEqual(ns.reconcile_teacher_inbox(), 0)
            self.assertEqual(self.writes, 1)

    def test_conflict_retries_from_fresh_registry_without_duplication(self):
        docs, leaves = self.sources()
        self.conflict_once = True
        with patch.object(ns, "private_read", self.read), \
             patch.object(ns, "private_write", self.write), \
             patch.object(ns, "load_registry", return_value=(docs, None)), \
             patch.object(ns, "load_leave_pass_registry", return_value=(leaves, None)):
            self.assertEqual(ns.reconcile_teacher_inbox(), 30)
            self.assertEqual(self.writes, 2)
            self.assertEqual(self.reads, 2)
            self.assertEqual(len({e["id"] for e in self.registry["events"]}), 30)

    def test_existing_read_and_superseded_history_preserved(self):
        docs, leaves = self.sources()
        first = dict(
            id=ns._event_id("DIRIGINTE", "CERERE_INVOIRE", "INVOIRE", "leave-0", "0"),
            schema_version=1, recipient="DIRIGINTE", event_type="CERERE_INVOIRE",
            source_type="INVOIRE", source_id="leave-0", source_revision="0",
            student_key="S1", read_at_utc="2026-11-12T08:00:00+00:00",
        )
        self.registry["events"].append(first)
        with patch.object(ns, "private_read", self.read), \
             patch.object(ns, "private_write", self.write), \
             patch.object(ns, "load_registry", return_value=(docs, None)), \
             patch.object(ns, "load_leave_pass_registry", return_value=(leaves, None)):
            self.assertEqual(ns.reconcile_teacher_inbox(), 30)
        prior = next(e for e in self.registry["events"] if e["id"] == first["id"])
        self.assertEqual(prior["read_at_utc"], first["read_at_utc"])
        self.assertEqual(prior["superseded_by_revision"], "1")
        self.assertTrue(prior["superseded_at_utc"])

    def test_duplicate_primary_leave_ids_fail_closed_without_write(self):
        docs, leaves = self.sources()
        leaves["requests"].append(dict(leaves["requests"][0]))
        with patch.object(ns, "private_read", self.read), \
             patch.object(ns, "private_write", self.write), \
             patch.object(ns, "load_registry", return_value=(docs, None)), \
             patch.object(ns, "load_leave_pass_registry", return_value=(leaves, None)):
            with self.assertRaises(ns.DocumentConflictError):
                ns.reconcile_teacher_inbox()
        self.assertEqual(self.writes, 0)


if __name__ == "__main__":
    unittest.main()
