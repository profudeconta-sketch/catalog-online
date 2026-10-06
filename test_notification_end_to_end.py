import json
import unittest
from unittest.mock import patch

import notification_storage as ns


class IntegratedNotificationCenterTests(unittest.TestCase):
    def setUp(self):
        self.state={"schema_version":1,"events":[]}
        self.sha="n0"

    def read(self,path):
        return json.dumps(self.state).encode("utf-8"),self.sha

    def write(self,path,raw,expected_sha,message):
        self.assertEqual(expected_sha,self.sha)
        self.state=json.loads(raw.decode("utf-8"))
        self.sha="n"+str(int(self.sha[1:])+1)
        return self.sha

    def test_parent_to_teacher_primary_sources_reconcile_idempotently(self):
        docs={"schema_version":1,"documents":[
            {"id":"parent-doc-1","direction":"PARINTE_SCOALA","student_key":"S1",
             "created_at_utc":"2026-10-06T10:00:00+00:00"}
        ]}
        leaves={"schema_version":1,"requests":[
            {"id":"leave-1","student_key":"S1","revision":1,
             "transmitted_at_utc":"2026-10-06T10:01:00+00:00"}
        ]}
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs,None)), \
             patch.object(ns,"load_leave_pass_registry",return_value=(leaves,None)):
            self.assertEqual(ns.reconcile_teacher_inbox(),2)
            self.assertEqual(ns.reconcile_teacher_inbox(),0)
            events=ns.list_notifications(recipient=ns.RECIPIENT_TEACHER)
            self.assertEqual(len(events),2)
            self.assertEqual(len(ns.list_notifications(
                recipient=ns.RECIPIENT_TEACHER,unread_only=True
            )),2)

    def test_school_to_parent_access_recovery_and_delivery_state_coexist(self):
        docs_unread={"schema_version":1,"documents":[
            {"id":"school-doc-1","direction":"SCOALA_PARINTE","student_key":"S1",
             "created_at_utc":"2026-10-06T11:00:00+00:00","first_accessed_at_utc":None}
        ]}
        docs_read={"schema_version":1,"documents":[
            {"id":"school-doc-1","direction":"SCOALA_PARINTE","student_key":"S1",
             "created_at_utc":"2026-10-06T11:00:00+00:00",
             "first_accessed_at_utc":"2026-10-06T11:05:00+00:00"}
        ]}
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs_unread,None)):
            self.assertEqual(ns.reconcile_parent_inbox("S1"),1)
            event=ns.list_notifications(recipient=ns.RECIPIENT_PARENT,student_key="S1")[0]
            ns.record_delivery(event["id"],ns.RECIPIENT_PARENT,"phone-a","queued","SM1")
            self.assertFalse(ns.delivery_needs_retry(
                event["id"],ns.RECIPIENT_PARENT,"phone-a"
            ))

        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs_read,None)):
            self.assertEqual(ns.reconcile_parent_inbox("S1"),0)
            events=ns.list_notifications(recipient=ns.RECIPIENT_PARENT,student_key="S1")
            self.assertEqual(len(events),1)
            self.assertIsNotNone(events[0]["read_at_utc"])
            self.assertEqual(events[0]["delivery_status"],"DELIVERED")
            self.assertIsNotNone(events[0]["delivered_at_utc"])
            self.assertEqual(ns.list_notifications(
                recipient=ns.RECIPIENT_PARENT,student_key="S1",unread_only=True
            ),[])

    def test_leave_revision_and_delivery_history_do_not_corrupt_each_other(self):
        docs={"schema_version":1,"documents":[]}
        v1={"schema_version":1,"requests":[
            {"id":"leave-1","student_key":"S1","revision":1,
             "transmitted_at_utc":"2026-10-06T10:00:00+00:00"}
        ]}
        v2={"schema_version":1,"requests":[
            {"id":"leave-1","student_key":"S1","revision":2,
             "transmitted_at_utc":"2026-10-06T10:10:00+00:00"}
        ]}
        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs,None)), \
             patch.object(ns,"load_leave_pass_registry",return_value=(v1,None)):
            ns.reconcile_teacher_inbox()
            old=ns.list_notifications(recipient=ns.RECIPIENT_TEACHER)[0]
            ns.record_delivery(old["id"],ns.RECIPIENT_TEACHER,"teacher-phone","sent","SM-OLD")

        with patch.object(ns,"private_read",self.read),patch.object(ns,"private_write",self.write), \
             patch.object(ns,"load_registry",return_value=(docs,None)), \
             patch.object(ns,"load_leave_pass_registry",return_value=(v2,None)):
            ns.reconcile_teacher_inbox()
            events=ns.list_notifications(recipient=ns.RECIPIENT_TEACHER)
            old=[e for e in events if e.get("source_revision")=="1"][0]
            current=[e for e in events if e.get("source_revision")=="2"][0]
            self.assertEqual(old["delivery_status"],"DELIVERED")
            self.assertIsNotNone(old.get("superseded_at_utc"))
            self.assertFalse(current.get("superseded_at_utc"))
            self.assertEqual(len(ns.list_notifications(
                recipient=ns.RECIPIENT_TEACHER,unread_only=True
            )),1)


if __name__=="__main__":
    unittest.main()
