from __future__ import annotations
import base64, datetime as dt, io, json, os, re, shutil, urllib.request, zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
import openpyxl

class PhotoImportError(RuntimeError): pass

@dataclass(frozen=True)
class ImportProposal:
    student_index:int; category:str; subject:str; kind:str; value:str; date:str
    motivated:bool=False; confidence:float=0.0; source_image:str=""
    verifiable:bool=True; verification_reason:str=""

def normalize_ddmm(value, year=2026):
    raw=str(value or "").strip().replace("/",".").replace("-",".")
    m=re.fullmatch(r"(\d{1,2})\.(\d{1,2})(?:\.(\d{2,4}))?",raw)
    if not m: raise PhotoImportError(f"Dată invalidă: {value!r}")
    y=int(m.group(3)) if m.group(3) else year
    if y<100:y+=2000
    return dt.date(y,int(m.group(2)),int(m.group(1))).strftime("%d.%m")

def date_in_period(ddmm,start,end):
    d=dt.datetime.strptime(normalize_ddmm(ddmm,start.year),"%d.%m").date().replace(year=start.year)
    return start<=d<=end

def safe_zip_images(data):
    if len(data)>80*1024*1024: raise PhotoImportError("Arhiva depășește 80 MB.")
    out=[]
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=[i for i in z.infolist() if not i.is_dir()]
        if len(infos)>80: raise PhotoImportError("Arhiva conține prea multe fișiere.")
        for i in infos:
            p=PurePosixPath(i.filename)
            if ".." in p.parts or p.is_absolute() or i.file_size>15*1024*1024: raise PhotoImportError("Fișier nesigur în arhivă.")
            if p.suffix.lower() in {".jpg",".jpeg",".png",".webp"}: out.append((p.name,z.read(i)))
    out.sort(key=lambda x:(int(re.findall(r"\d+",x[0])[-1]) if re.findall(r"\d+",x[0]) else 10**9,x[0]))
    if not out: raise PhotoImportError("Arhiva nu conține imagini.")
    return out

def pair_catalog_images(images,skip_cover=True):
    work=images[1:] if skip_cover and len(images)%2==1 else images
    if len(work)%2: raise PhotoImportError("Numărul fotografiilor stânga/dreapta nu este par.")
    return [(work[i],work[i+1]) for i in range(0,len(work),2)]

def _api_key():
    value=os.environ.get("OPENAI_API_KEY","")
    try:
        import streamlit as st
        value=value or str(st.secrets.get("OPENAI_API_KEY",""))
    except Exception: pass
    if not value: raise PhotoImportError("Lipsește OPENAI_API_KEY din Streamlit Secrets.")
    return value

def _data_url(name,data):
    mime={".png":"image/png",".webp":"image/webp"}.get(PurePosixPath(name).suffix.lower(),"image/jpeg")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"

def analyze_pair_with_vision(left,right,student_names,start,end,allowed_subjects):
    prompt=("Analizează două fotografii ale aceleiași deschideri de catalog școlar românesc. "
      f"Elevii de sus în jos sunt exact {json.dumps(student_names,ensure_ascii=False)}. "
      f"Folosește pentru subject NUMAI una dintre denumirile exacte: {json.dumps(allowed_subjects,ensure_ascii=False)}. "
      f"Extrage NUMAI note și absențe cu data lizibilă în intervalul {start:%d.%m.%Y}-{end:%d.%m.%Y}. "
      "Nu ghici și nu completa valori incerte. Răspunde STRICT JSON cu cheia records; fiecare record are "
      "student_index (0..2), category exact 'Cultură Generală' sau 'Module Tehnologice', subject, "
      "kind 'grade' sau 'absence', value (1..10 pentru grade), date DD.MM, motivated boolean, "
      "confidence 0..1, source_image 'left' sau 'right', legible boolean. "
      "legible=true NUMAI dacă studentul, disciplina, tipul, valoarea și data pot fi citite direct din fotografie, fără presupuneri. "
      "Dacă există orice dubiu, păstrează recordul, pune legible=false și confidence corespunzător; nu inventa valoarea.")
    payload={"model":"gpt-6-luna","input":[{"role":"user","content":[
      {"type":"input_text","text":prompt},
      {"type":"input_image","image_url":_data_url(left[0],left[1]),"detail":"high"},
      {"type":"input_image","image_url":_data_url(right[0],right[1]),"detail":"high"}]}]}
    req=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(payload).encode(),
      headers={"Authorization":f"Bearer {_api_key()}","Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=120) as resp: body=json.loads(resp.read().decode())
    except Exception as ex: raise PhotoImportError(f"Analiza imaginilor a eșuat: {type(ex).__name__}: {ex}") from ex
    txt=body.get("output_text","")
    if not txt:
        txt="\n".join(p.get("text","") for item in body.get("output",[]) for p in item.get("content",[]) if p.get("type")=="output_text")
    txt=str(txt).strip().strip(chr(96)).removeprefix("json").strip()
    try: rows=json.loads(txt).get("records",[])
    except Exception as ex: raise PhotoImportError("Răspunsul AI nu este JSON valid; importul a fost oprit.") from ex
    out=[]
    for r in rows:
        try:
            idx=int(r["student_index"]); kind=str(r["kind"]); date=normalize_ddmm(r["date"],start.year); conf=float(r.get("confidence",0))
            if not(0<=idx<len(student_names)) or kind not in {"grade","absence"} or not date_in_period(date,start,end): continue
            val=str(r.get("value","")).strip()
            if kind=="grade" and (not val.isdigit() or not 1<=int(val)<=10): continue
            legible=bool(r.get("legible",False))
            verifiable=legible and conf>=0.90
            reason="" if verifiable else "Citirea nu este suficient de clară pentru scriere automată; necesită verificare."
            out.append(ImportProposal(idx,str(r["category"]).strip(),str(r["subject"]).strip(),kind,val,date,bool(r.get("motivated",False)),conf,str(r.get("source_image","")),verifiable,reason))
        except Exception: continue
    return out


def _semantic_key(p):
    return (p.student_index,p.category.casefold(),p.subject.casefold(),p.kind,p.date,
            p.value if p.kind=="grade" else "",p.motivated)

def _parse_vision_records(body,student_names,start):
    txt=body.get("output_text","")
    if not txt:
        txt="\n".join(p.get("text","") for item in body.get("output",[])
                      for p in item.get("content",[]) if p.get("type")=="output_text")
    txt=str(txt).strip().strip(chr(96)).removeprefix("json").strip()
    try:
        return json.loads(txt).get("records",[])
    except Exception as ex:
        raise PhotoImportError("Răspunsul AI nu este JSON valid; verificarea a fost oprită.") from ex

def _vision_request(prompt,left,right,model="gpt-6-luna"):
    payload={"model":model,"input":[{"role":"user","content":[
        {"type":"input_text","text":prompt},
        {"type":"input_image","image_url":_data_url(left[0],left[1]),"detail":"high"},
        {"type":"input_image","image_url":_data_url(right[0],right[1]),"detail":"high"}]}]}
    req=urllib.request.Request("https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode(),
        headers={"Authorization":f"Bearer {_api_key()}","Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=120) as resp:
            return json.loads(resp.read().decode())
    except Exception as ex:
        raise PhotoImportError(f"Verificarea vizuală a eșuat: {type(ex).__name__}: {ex}") from ex

def recover_uncertain_proposals(left,right,student_names,start,end,allowed_subjects,items):
    """A doua citire independentă numai pentru cazurile neclare.
    Un caz devine verificabil doar prin consens semantic exact între două citiri lizibile.
    """
    uncertain=[p for p in items if not p.verifiable]
    targets=[{"student_index":p.student_index,"category":p.category,"subject":p.subject,
              "kind":p.kind,"value":p.value,"date":p.date,"motivated":p.motivated}
             for p in uncertain]
    prompt=("Efectuează o A DOUA citire independentă și COMPLETĂ a fotografiilor originale. "
      "Scopul este atât verificarea candidaților slabi, cât și detectarea oricărei înscrieri din perioada cerută "
      "care ar fi putut fi omisă la prima citire. Candidații slabi cunoscuți sunt: "
      f"{json.dumps(targets,ensure_ascii=False)}. "
      f"Elevii de sus în jos sunt {json.dumps(student_names,ensure_ascii=False)}. "
      f"Discipline permise: {json.dumps(allowed_subjects,ensure_ascii=False)}. "
      f"Perioada permisă: {start:%d.%m.%Y}-{end:%d.%m.%Y}. "
      "Pentru fiecare candidat răspunde STRICT JSON {\"records\":[...]}; fiecare record conține "
      "student_index, category, subject, kind, value, date DD.MM, motivated, confidence, source_image, legible. "
      "legible=true numai când toate câmpurile pot fi citite direct și fără inferență din fotografie. "
      "Dacă nu poți demonstra vizual o valoare, legible=false. Nu ghici.")
    rows=_parse_vision_records(_vision_request(prompt,left,right),student_names,start)
    second=[]
    for r in rows:
        try:
            idx=int(r["student_index"]); kind=str(r["kind"]); date=normalize_ddmm(r["date"],start.year)
            conf=float(r.get("confidence",0)); val=str(r.get("value","")).strip()
            if not(0<=idx<len(student_names)) or kind not in {"grade","absence"} or not date_in_period(date,start,end):
                continue
            if kind=="grade" and (not val.isdigit() or not 1<=int(val)<=10):
                continue
            legible=bool(r.get("legible",False))
            second.append(ImportProposal(idx,str(r["category"]).strip(),str(r["subject"]).strip(),
                kind,val,date,bool(r.get("motivated",False)),conf,str(r.get("source_image","")),
                legible and conf>=0.90,""))
        except Exception:
            continue
    first_by_key={_semantic_key(p):p for p in items}
    second_by_key={_semantic_key(p):p for p in second}
    recovered=[]
    all_keys=set(first_by_key)|set(second_by_key)
    for key in all_keys:
        p=first_by_key.get(key); q=second_by_key.get(key)
        if p is not None and q is not None and p.verifiable and q.verifiable:
            recovered.append(ImportProposal(p.student_index,p.category,p.subject,p.kind,p.value,p.date,
                p.motivated,max(p.confidence,q.confidence),p.source_image,True,
                "Demonstrat prin două citiri independente, complete și concordante ale fotografiei originale."))
        elif p is not None and q is not None and (p.verifiable or q.verifiable):
            base=p if p.verifiable else q
            recovered.append(ImportProposal(base.student_index,base.category,base.subject,base.kind,base.value,base.date,
                base.motivated,base.confidence,base.source_image,False,
                "Informația apare în ambele citiri, dar nu este demonstrată ca lizibilă independent în ambele."))
        else:
            base=p or q
            recovered.append(ImportProposal(base.student_index,base.category,base.subject,base.kind,base.value,base.date,
                base.motivated,base.confidence,base.source_image,False,
                "Informația apare într-o singură citire sau nu este lizibilă concordant; necesită recuperare/verificare suplimentară."))
    return recovered

def deduplicate_proposals(items):
    """O singură înregistrare per elev/disciplină/tip/dată; ambiguitățile se blochează."""
    groups={}
    for p in items:
        base=(p.student_index,p.category.casefold(),p.subject.casefold(),p.kind,p.date)
        groups.setdefault(base,[]).append(p)
    out=[]
    for rows in groups.values():
        semantics={(p.value if p.kind=="grade" else "", p.motivated) for p in rows}
        if len(semantics)!=1:
            # Două citiri diferite pentru aceeași rubrică și dată rămân vizibile, dar sunt blocate.
            best=max(rows,key=lambda p:p.confidence)
            out.append(ImportProposal(best.student_index,best.category,best.subject,best.kind,best.value,best.date,best.motivated,best.confidence,best.source_image,False,"Citiri contradictorii pentru aceeași rubrică; nu se poate demonstra valoarea."))
            continue
        out.append(max(rows,key=lambda p:p.confidence))
    return out

def _lookup(cg,th):
    return {(cat.casefold(),name.casefold()):(cat,name,col) for cat,items in (("Cultură Generală",cg),("Module Tehnologice",th)) for name,col in items}

def compare_with_workbook(path,elevi,cg,th,resolve,items):
    wb=openpyxl.load_workbook(path,data_only=False); lookup=_lookup(cg,th); out=[]
    try:
      for p in deduplicate_proposals(items):
        if not p.verifiable:
          out.append((p,"NECESITĂ_VERIFICARE",p.verification_reason or "Informația nu poate fi demonstrată ca lizibilă.")); continue
        mapped=lookup.get((p.category.casefold(),p.subject.casefold()))
        if not mapped: out.append((p,"NECUNOSCUT","Disciplina/modulul nu corespunde exact.")); continue
        cat,_,col=mapped; ws=wb[cat]; row=resolve(wb,elevi[p.student_index])
        if p.kind=="grade":
          existing=[(str(ws.cell(row,col+2*k).value or "").strip(),str(ws.cell(row,col+2*k+1).value or "").strip()) for k in range(10)]
          if (p.value,p.date) in existing: status,msg="DEJA_EXISTENT","Aceeași notă și dată există deja."
          elif any(d==p.date for _,d in existing): status,msg="CONFLICT","Există deja o notă la aceeași dată."
          else: status,msg="NOU","Poate fi adăugată după confirmare."
        else:
          target=p.date+("m" if p.motivated else ""); existing=[str(ws.cell(row,col+21+k).value or "").strip() for k in range(30)]
          if target in existing or (p.date in existing and not p.motivated): status,msg="DEJA_EXISTENT","Aceeași absență există deja; nu va fi dublată."
          elif p.motivated and p.date in existing: status,msg="CONFLICT","Absența există nemotivată; verifică motivarea."
          else: status,msg="NOU","Poate fi adăugată după confirmare."
        out.append((p,status,msg))
    finally: wb.close()
    return out

def apply_confirmed_import(path,elevi,cg,th,resolve,approved):
    # Barieră de siguranță la nivel de scriere: UI-ul nu poate ocoli regula adevărului demonstrabil.
    unsafe=[x for x in approved if x[1]!="NOU" or not x[0].verifiable]
    if unsafe: raise PhotoImportError("Scriere blocată: există înregistrări care nu sunt NOI și demonstrabil lizibile.")
    approved=[x for x in approved if x[1]=="NOU" and x[0].verifiable]
    if not approved:return 0,None
    backup=path+".photo-import.bak"; temp=path+".photo-import.tmp.xlsx"
    shutil.copy2(path,backup); shutil.copy2(path,temp); wb=openpyxl.load_workbook(temp); lookup=_lookup(cg,th); changed=0
    try:
      for p,_,_ in approved:
        cat,_,col=lookup[(p.category.casefold(),p.subject.casefold())]; ws=wb[cat]; row=resolve(wb,elevi[p.student_index])
        if p.kind=="grade":
          existing=[(str(ws.cell(row,col+2*k).value or "").strip(),str(ws.cell(row,col+2*k+1).value or "").strip()) for k in range(10)]
          if (p.value,p.date) in existing: continue
          if any(d==p.date for _,d in existing): raise PhotoImportError("Conflict apărut înainte de salvare.")
          for k in range(10):
            if ws.cell(row,col+2*k).value in (None,""):
              ws.cell(row,col+2*k).value=int(p.value); ws.cell(row,col+2*k+1).value=p.date; ws.cell(row,col+2*k+1).number_format="@"; changed+=1; break
          else: raise PhotoImportError("Nu există slot liber pentru notă.")
        else:
          target=p.date+("m" if p.motivated else ""); existing=[str(ws.cell(row,col+21+k).value or "").strip() for k in range(30)]
          if target in existing or (p.date in existing and not p.motivated): continue
          for k in range(30):
            if ws.cell(row,col+21+k).value in (None,""):
              ws.cell(row,col+21+k).value=target; ws.cell(row,col+21+k).number_format="@"; changed+=1; break
          else: raise PhotoImportError("Nu există slot liber pentru absență.")
      wb.save(temp); wb.close(); wb=None; os.replace(temp,path); return changed,backup
    except Exception:
      try:
        if wb: wb.close()
      finally:
        if os.path.exists(temp): os.remove(temp)
      shutil.copy2(backup,path); raise
