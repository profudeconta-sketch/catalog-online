import json, unittest
from unittest.mock import patch
import phone_delivery as pd

class _Resp:
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self): return json.dumps({"sid":"SM_TEST","status":"queued"}).encode()

class PhoneDeliveryTests(unittest.TestCase):
    def test_normalize_ro_phone(self):
        self.assertEqual(pd.normalize_ro_phone("0742 123 456"),"+40742123456")
        self.assertEqual(pd.normalize_ro_phone("0040 742 123 456"),"+40742123456")
        self.assertEqual(pd.normalize_ro_phone("+40 742 123 456"),"+40742123456")
        with self.assertRaises(ValueError): pd.normalize_ro_phone("123")
    def test_send_sms_uses_secrets_and_https(self):
        secrets={"TWILIO_ACCOUNT_SID":"AC_TEST","TWILIO_AUTH_TOKEN":"TOKEN","TWILIO_FROM_NUMBER":"+40111111111"}
        with patch.object(pd,"_secret",side_effect=lambda n:secrets.get(n,"")), patch.object(pd.urllib.request,"urlopen",return_value=_Resp()) as call:
            result=pd.send_sms("0742123456","Mesaj test")
            self.assertEqual(result["message_sid"],"SM_TEST")
            req=call.call_args.args[0]
            self.assertTrue(req.full_url.startswith("https://api.twilio.com/"))
            self.assertIn(b"To=%2B40742123456",req.data)
    def test_missing_config_fails_closed_without_network_or_cost(self):
        with patch.object(pd,"_secret",return_value=""), \
             patch.object(pd.urllib.request,"urlopen") as network:
            with self.assertRaises(pd.PhoneDeliveryError):
                pd.send_sms("0742123456","Mesaj")
            network.assert_not_called()

if __name__=="__main__": unittest.main()
