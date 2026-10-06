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
    def test_parent_unread_counter_uses_storage_semantics(self):
        p=self.parent
        section=p.index("reconcile_parent_inbox(_parent_student_key)")
        tabs=p.index("parent_tab_school",section)
        block=p[section:tabs]
        self.assertIn("unread_only=True",block)
        self.assertNotIn(
            '_parent_unread=[n for n in _parent_notifications if not n.get("read_at_utc")]',
            block,
        )

    def test_teacher_inbox_unread_counter_uses_storage_semantics(self):
        p=self.teacher
        inbox=p.index("# Inbox global diriginte")
        tabs=p.index("tab1, tab2",inbox)
        block=p[inbox:tabs]
        self.assertIn(
            "list_notifications(recipient=RECIPIENT_TEACHER,unread_only=True)",
            block,
        )
        self.assertNotIn(
            '_teacher_unread=[n for n in _teacher_notifications if not n.get("read_at_utc")]',
            block,
        )

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
    def test_whatsapp_is_manual_free_link_only(self):
        module=Path("whatsapp_delivery.py").read_text(encoding="utf-8").lower()
        self.assertIn("https://wa.me/",module)
        self.assertNotIn("twilio",module)
        self.assertNotIn("urlopen",module)
        self.assertNotIn("graph.facebook",module)

    def test_apps_do_not_import_or_send_sms(self):
        combined=(self.teacher+"\n"+self.parent).lower()
        self.assertNotIn("phone_delivery",combined)
        self.assertNotIn("send_sms",combined)
        self.assertNotIn("twilio",combined)

    def test_whatsapp_does_not_replace_internal_notification(self):
        self.assertIn("ensure_notification(recipient=RECIPIENT_PARENT",self.teacher)
        self.assertIn("ensure_notification(recipient=RECIPIENT_TEACHER",self.parent)
        self.assertIn("_parent_whatsapp_links",self.teacher)
        self.assertIn("_teacher_whatsapp_link",self.parent)


if __name__=="__main__": unittest.main()
