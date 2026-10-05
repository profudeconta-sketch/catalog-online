import datetime as dt
import os
import tempfile
import unittest
from openpyxl import Workbook, load_workbook
from catalog_photo_import import ImportProposal, PhotoImportError, normalize_ddmm, deduplicate_proposals, compare_with_workbook, apply_confirmed_import

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
