"""Prototip geometric A3 pentru deschiderea P3-P4.

Izolat de generatorul oficial si de datele primare. Nu citeste/scrie Excel,
nu sincronizeaza GitHub si nu persista nimic. Scop exclusiv: validare vizuala.
"""

from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import fontpkg

FONT = "CatalogA3Noto"
BOLD = "CatalogA3NotoBold"

P3 = (
    "Limba si literatura romana", "",
    "Limba moderna 1 - Limba engleza",
    "Limba moderna 2 - Limba franceza", "",
    "Matematica", "Fizica", "Chimie", "Biologie", "Istorie", "Geografie",
)
P4 = (
    "Logica, argumentare si comunicare", "Religie", "Educatie vizuala",
    "Educatie fizica si sport", "Tehnologia informatiei si a comunicatiilor (TIC)",
    "M1 - Bazele contabilitatii", "M2 - Etica si comunicare",
    "M3 - Structuri de primire turistica", "M4 - Procese si calitate in HoReCa",
    "M5 - CDEOS - Stagii de pregatire practica",
    "M6 - Curriculum pentru aprofundare si insertie profesionala", "", "", "",
)

def _fonts():
    path = str(fontpkg.path("Noto Sans"))
    if FONT not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT, path))
    if BOLD not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(BOLD, path))

def _wrap(text, max_chars=15):
    if not text:
        return ()
    words=text.split()
    lines=[]; cur=""
    for word in words:
        cand=(cur+" "+word).strip()
        if len(cand)<=max_chars:
            cur=cand
        else:
            if cur: lines.append(cur)
            cur=word
    if cur: lines.append(cur)
    return tuple(lines[:5])

def _subject_header(c, x, y0, w, h, label):
    c.rect(x,y0,w,h)
    sub_h=7*mm
    c.line(x,y0+sub_h,x+w,y0+sub_h)
    c.line(x+w/2,y0,x+w/2,y0+sub_h)
    c.setFont(FONT,4.0)
    c.drawCentredString(x+w*.25,y0+2.4*mm,"Absente")
    c.drawCentredString(x+w*.75,y0+2.4*mm,"Note")
    if label:
        lines=_wrap(label,14)
        fs=4.4 if len(lines)<=3 else 3.8
        c.setFont(BOLD,fs)
        total=(len(lines)-1)*4.5
        yy=y0+sub_h+(h-sub_h)/2+total/2
        for line in lines:
            c.drawCentredString(x+w/2,yy,line)
            yy-=4.5

def _identity(c,left,bottom,w,h,idx):
    c.rect(left,bottom,w,h)
    pad=3*mm
    top=bottom+h
    c.setFont(BOLD,6.2)
    c.drawString(left+pad,top-6*mm,f"{idx}. NUME PRENUME ELEV")
    c.setFont(FONT,4.7)
    c.drawString(left+pad,top-12*mm,"Nr. matricol ......................")
    c.drawString(left+pad,top-17*mm,"Trecut in registrul matricol vol. .... p. ....")
    c.line(left,top-21*mm,left+w,top-21*mm)
    c.setFont(BOLD,5.2)
    c.drawCentredString(left+w/2,top-26*mm,"SITUATIA SCOLARA")
    c.setFont(FONT,4.5)
    c.drawString(left+pad,top-32*mm,"La incheierea cursurilor ........................")
    c.drawString(left+pad,top-38*mm,"La incheierea anului scolar ...................")
    c.drawString(left+pad,top-44*mm,"Media generala .......................................")
    c.line(left,top-48*mm,left+w,top-48*mm)
    c.drawString(left+pad,top-54*mm,"Mentiuni (transferari, retrageri, amanari,")
    c.drawString(left+pad,top-59*mm,"corigente etc.) ........................................")

def generate(path):
    _fonts()
    W,H=landscape(A3)
    c=canvas.Canvas(path,pagesize=(W,H),pageCompression=1)
    margin=8*mm
    gutter=4*mm
    mid=W/2
    left0=margin
    left1=mid-gutter/2
    right0=mid+gutter/2
    right1=W-margin
    top=H-8*mm
    bottom=8*mm
    header_h=35*mm
    identity_w=49*mm
    terminal_w=24*mm

    c.setLineWidth(.45)
    c.setFont(BOLD,7)
    c.drawCentredString((left0+left1)/2,top-3*mm,"DISCIPLINELE/MODULELE*** DE")
    c.drawCentredString((right0+right1)/2,top-3*mm,"INVATAMANT")

    header_top=top-6*mm
    header_bottom=header_top-header_h
    c.rect(left0,header_bottom,identity_w,header_h)
    c.setFont(BOLD,13)
    c.drawCentredString(left0+identity_w/2,header_bottom+19*mm,"ELEVII")

    p3_start=left0+identity_w
    p3w=(left1-p3_start)/len(P3)
    for j,label in enumerate(P3):
        _subject_header(c,p3_start+j*p3w,header_bottom,p3w,header_h,label)

    p4_end=right1-terminal_w
    p4w=(p4_end-right0)/len(P4)
    for j,label in enumerate(P4):
        _subject_header(c,right0+j*p4w,header_bottom,p4w,header_h,label)
    c.rect(p4_end,header_bottom,terminal_w,header_h)
    c.setFont(BOLD,5)
    c.drawCentredString(p4_end+terminal_w/2,header_bottom+24*mm,"PURTARE / ABSENTE")
    c.setFont(FONT,4)
    c.drawCentredString(p4_end+terminal_w/2,header_bottom+15*mm,"Total / nemotivate")

    body_top=header_bottom
    body_bottom=bottom+4*mm
    block_h=(body_top-body_bottom)/3
    mean_h=13.5*mm
    for i in range(3):
        ytop=body_top-i*block_h
        ybot=ytop-block_h
        _identity(c,left0,ybot,identity_w,block_h,i+1)

        for j in range(len(P3)):
            x=p3_start+j*p3w
            c.rect(x,ybot,p3w,block_h)
            c.line(x+p3w/2,ybot+mean_h,x+p3w/2,ytop)
        for j in range(len(P4)):
            x=right0+j*p4w
            c.rect(x,ybot,p4w,block_h)
            c.line(x+p4w/2,ybot+mean_h,x+p4w/2,ytop)
        c.rect(p4_end,ybot,terminal_w,block_h)
        c.line(p4_end+10*mm,ybot,p4_end+10*mm,ytop)
        c.line(p4_end+17*mm,ybot,p4_end+17*mm,ytop)

        row_h=mean_h/3
        for k in (1,2):
            yy=ybot+k*row_h
            c.line(p3_start,yy,left1,yy)
            c.line(right0,yy,p4_end,yy)
            c.line(p4_end,yy,right1,yy)
        c.setFont(FONT,4.2)
        c.drawRightString(p3_start-2*mm,ybot+2*row_h+1.5*mm,"Media")
        c.drawRightString(p3_start-2*mm,ybot+row_h+1.5*mm,"Media la ex. de corig.")
        c.drawRightString(p3_start-2*mm,ybot+1.5*mm,"Media anuala")

    c.setDash(1,2)
    c.line(mid,bottom,mid,top)
    c.setDash()
    c.setFont(FONT,4.3)
    c.drawString(left0,bottom,"*** Prototip geometric A3 - fara date reale - pentru validarea P3-P4")
    c.save()

if __name__=="__main__":
    generate("catalog_p3_p4_a3_geometry.pdf")
