import datetime as dt
import os
import tempfile
import unittest
from openpyxl import Workbook, load_workbook
from catalog_photo_import import ImportProposal, PhotoImportError, normalize_ddmm, parse_absence_month_group, deduplicate_proposals, compare_with_workbook, apply_confirmed_import

CG=[("Matematică",8)]
TH=[]
ELEVI=[(1,"TEST","","1","")]

def resolve(_wb,_elev):
    return 13

def workbook():
    fd,path=tempfile.mkstemp(suffix=".xlsx"); os.close(fd)
    wb=Workbook(); ws=wb.active; ws.title="Cultură Generală"; wb.create_sheet("Module Tehnologice")
    wb.save(path); wb.close(); return path

class PhotoImportSafetyTests(unittest.TestCase):
    def test_dates(self):
        self.assertEqual(normalize_ddmm("2/10"),"02.10")
        self.assertEqual(normalize_ddmm("30-9"),"30.09")
        self.assertEqual(normalize_ddmm("30/IX"),"30.09")
        self.assertEqual(normalize_ddmm("1.X"),"01.10")
        self.assertEqual(normalize_ddmm("02-X-2026"),"02.10")
        self.assertEqual(normalize_ddmm(" 2 / x "), "02.10")

    def test_roman_month_validation(self):
        for bad in ("2/XIII","2/IIII","31/IX","0/X","2/ABC"):
            with self.assertRaises(PhotoImportError, msg=bad):
                normalize_ddmm(bad)

    def test_roman_month_period_filter(self):
        from catalog_photo_import import date_in_period
        start=dt.date(2026,9,30); end=dt.date(2026,10,2)
        self.assertTrue(date_in_period("30/IX",start,end))
        self.assertTrue(date_in_period("1/X",start,end))
        self.assertTrue(date_in_period("02/X",start,end))
        self.assertFalse(date_in_period("29/IX",start,end))
        self.assertFalse(date_in_period("3/X",start,end))

    def test_absence_roman_month_group(self):
        self.assertEqual(parse_absence_month_group("X: 1, 2, 5"),["01.10","02.10","05.10"])
        self.assertEqual(parse_absence_month_group("X: 1 2 5"),["01.10","02.10","05.10"])
        self.assertEqual(parse_absence_month_group(" IX : 30 "),["30.09"])
        self.assertEqual(parse_absence_month_group("XI: 3,7 12"),["03.11","07.11","12.11"])

    def test_absence_group_never_concatenates_space_separated_days(self):
        self.assertEqual(parse_absence_month_group("X: 1 2"),["01.10","02.10"])
        self.assertNotEqual(parse_absence_month_group("X: 1 2"),["12.10"])

    def test_absence_group_rejects_invalid_or_ambiguous_content(self):
        for bad in ("XIII: 1","IIII: 2","X: 32","IX: 31","X:","X: 1/2","X: 2 2"):
            with self.assertRaises(PhotoImportError, msg=bad):
                parse_absence_month_group(bad)

    def test_contradiction_stays_visible_and_blocked(self):
        a=ImportProposal(0,"Cultură Generală","Matematică","grade","8","02.10",confidence=.98,verifiable=True)
        b=ImportProposal(0,"Cultură Generală","Matematică","grade","9","02.10",confidence=.99,verifiable=True)
        out=deduplicate_proposals([a,b])
        self.assertEqual(len(out),1)
        self.assertFalse(out[0].verifiable)


    def test_verified_consensus_survives_single_unverified_disagreement(self):
        agreed=ImportProposal(0,"Cultură Generală","Matematică","grade","8","02.10",confidence=.96,verifiable=True)
        isolated=ImportProposal(0,"Cultură Generală","Matematică","grade","9","02.10",confidence=.99,verifiable=False)
        out=deduplicate_proposals([agreed,isolated])
        self.assertEqual(len(out),1)
        self.assertTrue(out[0].verifiable)
        self.assertEqual(out[0].value,"8")

    def test_unverifiable_is_not_new(self):
        path=workbook()
        try:
            p=ImportProposal(0,"Cultură Generală","Matematică","grade","8","02.10",confidence=.99,verifiable=False)
            result=compare_with_workbook(path,ELEVI,CG,TH,resolve,[p])
            self.assertEqual(result[0][1],"NECESITĂ_VERIFICARE")
        finally: os.remove(path)

    def test_write_gate_rejects_unverifiable(self):
        path=workbook()
        try:
            p=ImportProposal(0,"Cultură Generală","Matematică","grade","8","02.10",confidence=.99,verifiable=False)
            with self.assertRaises(PhotoImportError):
                apply_confirmed_import(path,ELEVI,CG,TH,resolve,[(p,"NOU","")])
            wb=load_workbook(path); self.assertIsNone(wb["Cultură Generală"].cell(13,8).value); wb.close()
        finally: os.remove(path)

    def test_write_then_duplicate_detection(self):
        path=workbook()
        try:
            p=ImportProposal(0,"Cultură Generală","Matematică","grade","8","02.10",confidence=.99,verifiable=True)
            before=compare_with_workbook(path,ELEVI,CG,TH,resolve,[p]); self.assertEqual(before[0][1],"NOU")
            changed,backup=apply_confirmed_import(path,ELEVI,CG,TH,resolve,before); self.assertEqual(changed,1)
            after=compare_with_workbook(path,ELEVI,CG,TH,resolve,[p]); self.assertEqual(after[0][1],"DEJA_EXISTENT")
            if backup and os.path.exists(backup): os.remove(backup)
        finally: os.remove(path)

if __name__=="__main__":
    unittest.main()
