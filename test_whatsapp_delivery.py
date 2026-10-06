import unittest
from unittest.mock import patch
import whatsapp_delivery as wd

class WhatsAppDeliveryTests(unittest.TestCase):
    def test_normalize_ro_phone(self):
        self.assertEqual(wd.normalize_ro_phone("0742 123 456"),"+40742123456")
        self.assertEqual(wd.normalize_ro_phone("0040 742 123 456"),"+40742123456")
        with self.assertRaises(ValueError):
            wd.normalize_ro_phone("123")

    def test_link_is_free_manual_wa_me_link(self):
        link=wd.whatsapp_link("0742123456","Mesaj test")
        self.assertTrue(link.startswith("https://wa.me/40742123456?text="))
        self.assertIn("Mesaj%20test",link)

    def test_module_has_no_paid_api_or_network_client(self):
        source=open("whatsapp_delivery.py","r",encoding="utf-8").read().lower()
        self.assertNotIn("twilio",source)
        self.assertNotIn("urlopen",source)
        self.assertNotIn("requests.",source)
        self.assertNotIn("graph.facebook",source)
        self.assertNotIn("whatsapp_business",source)

    def test_teacher_phone_is_optional(self):
        with patch.dict("os.environ",{},clear=True):
            with patch("whatsapp_delivery.os.environ.get",return_value=None):
                self.assertIsNone(wd.teacher_phone())

if __name__=="__main__":
    unittest.main()
