import hashlib
import json
import unittest
from unittest.mock import patch

import document_storage as ds


class SchoolDocumentAccessTests(unittest.TestCase):
    def setUp(self):
        self.student_rm="RM-TEST-1"
        self.student_key=ds.normalize_student_key(self.student_rm)
        self.source_id="a"*32
        self.source={
            "id":self.source_id,
            "schema_version":1,
            "student_key":self.student_key,
            "school_year":"2026-2027",
            "direction":"SCOALA_PARINTE",
            "category":"SCOALA_CATRE_PARINTE",
            "document_type":"INSTIINTARE",
            "original_filename":"instiintare.pdf",
            "stored_path":"documente_scolare/2026-2027/x/source.pdf",
            "mime_type":"application/pdf",
            "size_bytes":10,
            "sha256":"x",
            "sender_role":"SCOALA",
            "recipient_role":"PARINTE",
            "created_at_utc":"2026-10-06T10:00:00+00:00",
            "status":"NECITIT",
            "first_accessed_at_utc":None,
        }
        self.registry={"schema_version":1,"documents":[dict(self.source)]}
        self.registry_sha="registry-0"
        self.files={}

    def private_read(self,path):
        if path==ds.REGISTRY_PATH:
            return json.dumps(self.registry).encode("utf-8"),self.registry_sha
        value=self.files.get(path)
        if value is None:
            return None,None
        return value,hashlib.sha256(value).hexdigest()

    def private_write(self,path,content,expected_sha=None,message=""):
        if path==ds.REGISTRY_PATH:
            if expected_sha!=self.registry_sha:
                raise ds.DocumentConflictError("conflict")
            self.registry=json.loads(bytes(content).decode("utf-8"))
            self.registry_sha="registry-1"
            return self.registry_sha
        if expected_sha is None and path in self.files:
            raise ds.DocumentConflictError("exists")
        self.files[path]=bytes(content)
        return hashlib.sha256(bytes(content)).hexdigest()

    def _run_access(self,rm=None):
        fake_pdf=b"%PDF-1.4\nreceipt\n%%EOF"
        with patch.object(ds,"private_read",self.private_read), \
             patch.object(ds,"private_write",self.private_write), \
             patch.object(ds,"generate_school_document_receipt_pdf",return_value=fake_pdf):
            return ds.register_first_school_document_access(
                student_rm_pg=rm or self.student_rm,
                student_name="Elev Test",
                document_id=self.source_id,
            )

    def test_first_access_marks_source_and_creates_one_confirmation(self):
        result=self._run_access()
        self.assertTrue(result["created"])
        source=[x for x in self.registry["documents"] if x["id"]==self.source_id][0]
        confirmations=[x for x in self.registry["documents"] if x.get("category")=="CONFIRMARE_PRIMIRE"]
        self.assertEqual(source["status"],"CITIT")
        self.assertIsNotNone(source["first_accessed_at_utc"])
        self.assertEqual(len(confirmations),1)
        self.assertEqual(source["confirmation_document_id"],confirmations[0]["id"])
        self.assertEqual(confirmations[0]["source_document_id"],self.source_id)

    def test_second_access_is_idempotent_and_does_not_duplicate_receipt(self):
        first=self._run_access()
        second=self._run_access()
        confirmations=[x for x in self.registry["documents"] if x.get("category")=="CONFIRMARE_PRIMIRE"]
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(len(confirmations),1)
        self.assertEqual(
            first["confirmation_document"]["id"],
            second["confirmation_document"]["id"],
        )

    def test_registry_conflict_retries_without_duplicate_or_different_receipt(self):
        fake_pdf=b"%PDF-1.4\nreceipt\n%%EOF"
        writes={"registry":0}

        def conflict_once(path,content,expected_sha=None,message=""):
            if path==ds.REGISTRY_PATH:
                writes["registry"]+=1
                if writes["registry"]==1:
                    self.registry_sha="registry-concurrent"
                    raise ds.DocumentConflictError("simulated concurrent update")
            return self.private_write(path,content,expected_sha,message)

        with patch.object(ds,"private_read",self.private_read), \
             patch.object(ds,"private_write",conflict_once), \
             patch.object(ds,"generate_school_document_receipt_pdf",return_value=fake_pdf):
            result=ds.register_first_school_document_access(
                student_rm_pg=self.student_rm,
                student_name="Elev Test",
                document_id=self.source_id,
            )

        confirmations=[x for x in self.registry["documents"] if x.get("category")=="CONFIRMARE_PRIMIRE"]
        self.assertTrue(result["created"])
        self.assertEqual(writes["registry"],2)
        self.assertEqual(len(confirmations),1)
        self.assertEqual(len(self.files),1)
        self.assertEqual(confirmations[0]["source_document_id"],self.source_id)

    def test_access_is_rejected_for_another_authenticated_student(self):
        with self.assertRaises(ds.DocumentStorageError):
            self._run_access("RM-OTHER")
        self.assertEqual(len(self.registry["documents"]),1)
        self.assertIsNone(self.registry["documents"][0]["first_accessed_at_utc"])
        self.assertEqual(self.files,{})


if __name__=="__main__":
    unittest.main()
