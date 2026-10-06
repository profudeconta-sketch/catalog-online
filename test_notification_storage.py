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
if __name__=="__main__": unittest.main()
