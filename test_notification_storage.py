import unittest
from unittest.mock import patch
import notification_storage as ns

class NotificationStorageTests(unittest.TestCase):
    def setUp(self):
        self.state={"schema_version":1,"events":[]}; self.sha="s0"
    def read(self,path):
        import json
        return json.dumps(self.state).encode(),self.sha
    def write(self,path,raw,expected_sha,message):
        import json
        self.assertEqual(expected_sha,self.sha)
        self.state=json.loads(raw); self.sha="s1"; return self.sha
    def test_idempotent_event(self):
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write):
            a,created=ns.ensure_notification(recipient="DIRIGINTE",event_type="DOCUMENT_NOU",source_type="DOCUMENT",source_id="d1",student_key="S1")
            b,created2=ns.ensure_notification(recipient="DIRIGINTE",event_type="DOCUMENT_NOU",source_type="DOCUMENT",source_id="d1",student_key="S1")
            self.assertTrue(created); self.assertFalse(created2); self.assertEqual(a["id"],b["id"]); self.assertEqual(len(self.state["events"]),1)
    def test_revision_creates_new_leave_event(self):
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write):
            ns.ensure_notification(recipient="DIRIGINTE",event_type="INVOIRE_NOUA",source_type="LEAVE",source_id="l1",source_revision=1,student_key="S1")
            ns.ensure_notification(recipient="DIRIGINTE",event_type="INVOIRE_NOUA",source_type="LEAVE",source_id="l1",source_revision=2,student_key="S1")
            self.assertEqual(len(self.state["events"]),2)
    def test_mark_read_is_idempotent(self):
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write):
            e,_=ns.ensure_notification(recipient="DIRIGINTE",event_type="X",source_type="D",source_id="1",student_key="S")
            _,first=ns.mark_notification_read(e["id"],"DIRIGINTE"); _,second=ns.mark_notification_read(e["id"],"DIRIGINTE")
            self.assertTrue(first); self.assertFalse(second)
    def test_reconcile_derives_documents_and_leave_revisions(self):
        docs={"schema_version":1,"documents":[
            {"id":"d1","direction":"PARINTE_SCOALA","student_key":"S1","created_at_utc":"2026-10-06T10:00:00+00:00"},
            {"id":"d2","direction":"SCOALA_PARINTE","student_key":"S1","created_at_utc":"2026-10-06T10:01:00+00:00"},
        ]}
        leaves={"schema_version":1,"requests":[
            {"id":"l1","student_key":"S1","revision":2,"transmitted_at_utc":"2026-10-06T10:02:00+00:00"}
        ]}
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs,None)), \
             patch.object(ns,"load_leave_pass_registry",return_value=(leaves,None)):
            self.assertEqual(ns.reconcile_teacher_inbox(),2)
            self.assertEqual(ns.reconcile_teacher_inbox(),0)
            events=ns.list_notifications(recipient=ns.RECIPIENT_TEACHER)
            self.assertEqual(len(events),2)
            self.assertEqual({e["event_type"] for e in events},{"DOCUMENT_PARINTE","CERERE_INVOIRE"})

    def test_reconcile_supersedes_old_leave_revision_without_losing_history(self):
        docs={"schema_version":1,"documents":[]}
        leaves_v1={"schema_version":1,"requests":[
            {"id":"l1","student_key":"S1","revision":1,"transmitted_at_utc":"2026-10-06T10:00:00+00:00"}
        ]}
        leaves_v2={"schema_version":1,"requests":[
            {"id":"l1","student_key":"S1","revision":2,"transmitted_at_utc":"2026-10-06T10:05:00+00:00"}
        ]}
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs,None)), \
             patch.object(ns,"load_leave_pass_registry",return_value=(leaves_v1,None)):
            self.assertEqual(ns.reconcile_teacher_inbox(),1)
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs,None)), \
             patch.object(ns,"load_leave_pass_registry",return_value=(leaves_v2,None)):
            self.assertEqual(ns.reconcile_teacher_inbox(),1)
            all_events=ns.list_notifications(recipient=ns.RECIPIENT_TEACHER)
            unread=ns.list_notifications(recipient=ns.RECIPIENT_TEACHER,unread_only=True)
            self.assertEqual(len(all_events),2)
            self.assertEqual(len(unread),1)
            old=[e for e in all_events if e.get("source_revision")=="1"][0]
            current=[e for e in all_events if e.get("source_revision")=="2"][0]
            self.assertEqual(old.get("superseded_by_revision"),"2")
            self.assertIsNotNone(old.get("superseded_at_utc"))
            self.assertFalse(current.get("superseded_at_utc"))

    def test_parent_notification_is_derived_only_from_school_documents(self):
        docs={"schema_version":1,"documents":[
            {"id":"s1","direction":"SCOALA_PARINTE","student_key":"S1","created_at_utc":"2026-10-06T11:00:00+00:00"},
            {"id":"p1","direction":"PARINTE_SCOALA","student_key":"S1","created_at_utc":"2026-10-06T11:01:00+00:00"},
            {"id":"s2","direction":"SCOALA_PARINTE","student_key":"S2","created_at_utc":"2026-10-06T11:02:00+00:00"},
        ]}
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs,None)):
            self.assertEqual(ns.reconcile_parent_inbox("S1"),1)
            self.assertEqual(ns.reconcile_parent_inbox("S1"),0)
            events=ns.list_notifications(recipient=ns.RECIPIENT_PARENT,student_key="S1")
            self.assertEqual(len(events),1)
            event,changed=ns.mark_parent_source_read("S1","s1")
            self.assertTrue(changed)
            self.assertIsNotNone(event["read_at_utc"])
            _,changed2=ns.mark_parent_source_read("S1","s1")
            self.assertFalse(changed2)

    def test_parent_reconcile_repairs_unread_notification_after_primary_access(self):
        docs_unread={"schema_version":1,"documents":[
            {"id":"s1","direction":"SCOALA_PARINTE","student_key":"S1",
             "created_at_utc":"2026-10-06T11:00:00+00:00","first_accessed_at_utc":None}
        ]}
        docs_accessed={"schema_version":1,"documents":[
            {"id":"s1","direction":"SCOALA_PARINTE","student_key":"S1",
             "created_at_utc":"2026-10-06T11:00:00+00:00",
             "first_accessed_at_utc":"2026-10-06T11:05:00+00:00"}
        ]}
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs_unread,None)):
            self.assertEqual(ns.reconcile_parent_inbox("S1"),1)
            self.assertEqual(len(ns.list_notifications(
                recipient=ns.RECIPIENT_PARENT,student_key="S1",unread_only=True
            )),1)
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs_accessed,None)):
            self.assertEqual(ns.reconcile_parent_inbox("S1"),0)
            events=ns.list_notifications(recipient=ns.RECIPIENT_PARENT,student_key="S1")
            self.assertEqual(len(events),1)
            self.assertIsNotNone(events[0].get("read_at_utc"))
            self.assertEqual(ns.list_notifications(
                recipient=ns.RECIPIENT_PARENT,student_key="S1",unread_only=True
            ),[])

    def test_delivery_records_first_success_timestamp_and_preserves_it(self):
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write):
            event,_=ns.ensure_notification(
                recipient=ns.RECIPIENT_PARENT,event_type="X",source_type="D",
                source_id="1",student_key="S1"
            )
            pending=ns.record_delivery(event["id"],ns.RECIPIENT_PARENT,"phone-a","failed")
            self.assertEqual(pending["delivery_status"],"PENDING")
            self.assertIsNone(pending.get("delivered_at_utc"))
            delivered=ns.record_delivery(event["id"],ns.RECIPIENT_PARENT,"phone-a","queued","SM1")
            first_at=delivered.get("delivered_at_utc")
            self.assertEqual(delivered["delivery_status"],"DELIVERED")
            self.assertIsNotNone(first_at)
            repeated=ns.record_delivery(event["id"],ns.RECIPIENT_PARENT,"phone-a","delivered","SM1")
            self.assertEqual(repeated.get("delivered_at_utc"),first_at)

    def test_delivery_retry_is_allowed_only_until_success_for_same_destination(self):
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write):
            event,_=ns.ensure_notification(
                recipient=ns.RECIPIENT_PARENT,event_type="X",source_type="D",
                source_id="retry-1",student_key="S1"
            )
            self.assertTrue(ns.delivery_needs_retry(
                event["id"],ns.RECIPIENT_PARENT,"phone-a"
            ))
            ns.record_delivery(event["id"],ns.RECIPIENT_PARENT,"phone-a","failed")
            self.assertTrue(ns.delivery_needs_retry(
                event["id"],ns.RECIPIENT_PARENT,"phone-a"
            ))
            ns.record_delivery(event["id"],ns.RECIPIENT_PARENT,"phone-a","queued","SM1")
            self.assertFalse(ns.delivery_needs_retry(
                event["id"],ns.RECIPIENT_PARENT,"phone-a"
            ))
            self.assertTrue(ns.delivery_needs_retry(
                event["id"],ns.RECIPIENT_PARENT,"phone-b"
            ))

    def test_failed_delivery_does_not_erase_another_successful_delivery(self):
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write):
            event,_=ns.ensure_notification(
                recipient=ns.RECIPIENT_PARENT,event_type="X",source_type="D",
                source_id="2",student_key="S1"
            )
            ns.record_delivery(event["id"],ns.RECIPIENT_PARENT,"phone-a","sent","SM1")
            result=ns.record_delivery(event["id"],ns.RECIPIENT_PARENT,"phone-b","failed")
            self.assertEqual(result["delivery_status"],"DELIVERED")
            self.assertIsNotNone(result.get("delivered_at_utc"))
            self.assertEqual(result["deliveries"]["phone-b"]["status"],"failed")

    def test_academic_update_notifies_once_per_verified_version(self):
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write):
            args=dict(recipient=ns.RECIPIENT_PARENT,event_type="SITUATIE_SCOLARA_ACTUALIZATA",
                      source_type="CATALOG",source_id="S1",student_key="S1")
            _,first=ns.ensure_notification(**args,source_revision="hash-a")
            _,duplicate=ns.ensure_notification(**args,source_revision="hash-a")
            _,changed=ns.ensure_notification(**args,source_revision="hash-b")
            self.assertTrue(first); self.assertFalse(duplicate); self.assertTrue(changed)
            self.assertEqual(len(self.state["events"]),2)

if __name__=="__main__": unittest.main()
