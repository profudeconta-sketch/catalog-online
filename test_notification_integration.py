import unittest
from pathlib import Path

class NotificationIntegrationGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.teacher=Path("app_web_catalog.py").read_text(encoding="utf-8")
        cls.parent=Path("app_parinti.py").read_text(encoding="utf-8")
    def test_parent_upload_primary_write_precedes_alert(self):
        p=self.parent
        write=p.index("store_new_document(record, validated_bytes)")
        alert=p.index("_register_teacher_alert(",write)
        self.assertLess(write,alert)
    def test_leave_primary_write_precedes_alert(self):
        p=self.parent
        submit=p.index("_leave_record=submit_or_reformulate_leave_request(")
        alert=p.index("_register_teacher_alert(",submit)
        self.assertLess(submit,alert)
    def test_school_document_primary_write_precedes_parent_alert(self):
        p=self.teacher
        section=p.index("teacher_send_school_document")
        write=p.index("store_new_document(record, validated_content)",section)
        alert=p.index("_register_parent_alert(",write)
        self.assertLess(write,alert)
    def test_receipt_remains_bound_to_real_document_access(self):
        p=self.parent
        open_button=p.index("Deschide documentul și confirmă luarea la cunoștință")
        receipt=p.index("register_first_school_document_access(",open_button)
        mark=p.index("mark_parent_source_read(",receipt)
        self.assertLess(open_button,receipt)
        self.assertLess(receipt,mark)
    def test_teacher_inbox_has_no_manual_mark_read_button(self):
        p=self.teacher
        inbox=p.index("# Inbox global diriginte")
        tabs=p.index("tab1, tab2",inbox)
        block=p[inbox:tabs]
        self.assertNotIn("Marchează ca văzut",block)

    def test_teacher_document_read_requires_validated_source_access(self):
        p=self.teacher
        inbox=p.index("# Inbox global diriginte")
        source=p.index("read_registered_document(_student_key,_source_id)",inbox)
        mark=p.index('mark_notification_read(_n["id"],RECIPIENT_TEACHER)',source)
        self.assertLess(source,mark)

    def test_teacher_leave_read_requires_exact_notified_revision(self):
        p=self.teacher
        inbox=p.index("# Inbox global diriginte")
        source=p.index("load_leave_pass_registry()",inbox)
        revision=p.index('str(item.get("revision",1))==str(_n.get("source_revision") or 1)',source)
        mark=p.index('mark_notification_read(_n["id"],RECIPIENT_TEACHER)',revision)
        self.assertLess(source,revision)
        self.assertLess(revision,mark)

    def test_academic_alert_requires_explicit_button(self):
        p=self.teacher
        button=p.index("Informează părintele despre actualizarea situației școlare")
        event=p.index('event_type="SITUATIE_SCOLARA_ACTUALIZATA"',button)
        self.assertLess(button,event)
    def test_phone_numbers_are_not_hardcoded_in_delivery_module(self):
        p=Path("phone_delivery.py").read_text(encoding="utf-8")
        self.assertNotIn("0742",p)
        self.assertIn('TEACHER_PHONE',p)
        self.assertIn('TWILIO_ACCOUNT_SID',p)

if __name__=="__main__": unittest.main()
