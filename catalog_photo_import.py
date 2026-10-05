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

_ROMAN_MONTHS={"I":1,"II":2,"III":3,"IV":4,"V":5,"VI":6,"VII":7,"VIII":8,"IX":9,"X":10,"XI":11,"XII":12}

def normalize_ddmm(value, year=2026):
    raw=str(value or "").strip().upper().replace("/",".").replace("-",".")
    raw=re.sub(r"\s+","",raw)
    m=re.fullmatch(r"(\d{1,2})\.([0-9]{1,2}|[IVX]+)(?:\.(\d{2,4}))?",raw)
    if not m: raise PhotoImportError(f"Dată invalidă: {value!r}")
    month_token=m.group(2)
    if month_token.isdigit():
        month=int(month_token)
    else:
        month=_ROMAN_MONTHS.get(month_token)
        if month is None:
            raise PhotoImportError(f"Lună romană invalidă în data: {value!r}")
    y=int(m.group(3)) if m.group(3) else year
    if y<100:y+=2000
    try:
        return dt.date(y,month,int(m.group(1))).strftime("%d.%m")
    except ValueError as ex:
        raise PhotoImportError(f"Dată calendaristică invalidă: {value!r}") from ex

def date_in_period(ddmm,start,end):
    d=dt.datetime.strptime(normalize_ddmm(ddmm,start.year),"%d.%m").date().replace(year=start.year)
    return start<=d<=end


def parse_absence_month_group(value, year=2026):
    """Transformă notația fizică de tip 'X: 1, 2 5,17' în date DD.MM.
    Luna romană este declarată o singură dată; fiecare număr arab ulterior este o zi.
    """
    raw=str(value or "").strip().upper()
    m=re.fullmatch(r"\s*([IVX]+)\s*:\s*(.*?)\s*",raw)
    if not m:
        raise PhotoImportError(f"Grup de absențe invalid: {value!r}")
    month=_ROMAN_MONTHS.get(m.group(1))
    if month is None:
        raise PhotoImportError(f"Lună romană invalidă în grupul de absențe: {value!r}")
    days_raw=m.group(2)
    if not days_raw:
        raise PhotoImportError(f"Grup de absențe fără zile: {value!r}")
    # În catalog zilele pot fi delimitate prin virgulă, punct și virgulă sau doar spațiu.
    # Nu concatenăm cifre separate: "1 2" înseamnă zilele 1 și 2, nu ziua 12.
    if re.search(r"[^\d,\s;]",days_raw):
        raise PhotoImportError(f"Separator sau caracter invalid în grupul de absențe: {value!r}")
    tokens=re.findall(r"\d{1,2}",days_raw)
    residue=re.sub(r"\d{1,2}|[,;\s]","",days_raw)
    if residue or not tokens:
        raise PhotoImportError(f"Zile invalide în grupul de absențe: {value!r}")
    out=[]
    seen=set()
    for token in tokens:
        day=int(token)
        try:
            ddmm=dt.date(year,month,day).strftime("%d.%m")
        except ValueError as ex:
            raise PhotoImportError(f"Zi calendaristică invalidă în grupul de absențe: {token!r}") from ex
        if ddmm in seen:
            raise PhotoImportError(f"Zi repetată în același grup de absențe: {ddmm}")
        seen.add(ddmm); out.append(ddmm)
    return out


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
    # Coperta este o alegere explicită a fluxului, nu o deducție din paritatea numărului de imagini.
    work=images[1:] if skip_cover else images
    if len(work)%2:
        raise PhotoImportError("După tratarea explicită a copertei, numărul fotografiilor stânga/dreapta nu este par.")
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
      "Pentru ABSENȚE, catalogul fizic poate scrie luna o singură dată cu cifre romane urmată de două puncte, de exemplu 'X: 1, 2 5'. "
      "În acest caz X este luna octombrie, iar 1, 2 și 5 sunt trei zile distincte; spațiul dintre 2 și 5 este separator, nu formează 25. "
      "Emite câte un record separat pentru fiecare zi, cu data normalizată DD.MM. "
      "Pentru NOTE, înscrierea fizică poate avea forma NOTĂ/ZI, iar luna poate fi indicată contextual în ACEEAȘI rubrică. "
      "Acceptă data numai dacă luna este demonstrabilă vizual în aceeași rubrică; nu transfera luna de la alt elev, altă disciplină sau altă rubrică. "
      "Dacă se vede numai ziua, dar luna nu poate fi demonstrată, păstrează recordul cu legible=false; NU presupune luna din intervalul cerut. "
      "Dacă există orice dubiu, păstrează recordul, pune legible=false și confidence corespunzător; nu inventa valoarea.")
    model=os.environ.get("OPENAI_VISION_MODEL","gpt-6-luna")
    payload={"model":model,"input":[{"role":"user","content":[
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

def _vision_request(prompt,left,right,model=None):
    model=model or os.environ.get("OPENAI_VISION_MODEL","gpt-6-luna")
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
    """Până la trei citiri independente. Două citiri lizibile și semantic identice sunt
    necesare pentru promovarea automată; a treia citire rulează numai pentru cazurile
    fără consens după primele două.
    """
    def read_pass(pass_no, targets, complete=False):
        scope=("o citire COMPLETĂ a ambelor pagini, inclusiv înscrieri omise anterior"
               if complete else "o reverificare focalizată a candidaților nerezolvați")
        target_hint="" if complete else (
          "Reverifică numai aceste poziții structurale, FĂRĂ a primi valoarea sau data citită anterior: "
          + json.dumps(targets,ensure_ascii=False) + ". "
        )
        prompt=(f"Efectuează a {pass_no}-a citire independentă: {scope}. "
          f"{target_hint}"
          f"Elevii de sus în jos sunt {json.dumps(student_names,ensure_ascii=False)}. "
          f"Discipline permise: {json.dumps(allowed_subjects,ensure_ascii=False)}. "
          f"Perioada permisă: {start:%d.%m.%Y}-{end:%d.%m.%Y}. "
          "Răspunde STRICT JSON {\"records\":[...]}; fiecare record conține student_index, category, "
          "subject, kind, value, date DD.MM, motivated, confidence, source_image, legible. "
          "Pentru ABSENȚE, luna poate apărea o singură dată ca cifră romană urmată de ':', iar zilele arabe care urmează în ACEEAȘI rubrică aparțin acelei luni; "
          "virgula sau spațiul separă zile distincte (de ex. 'X: 1 2' = 01.10 și 02.10, NU 12.10). "
          "Nu transfera niciodată luna între elevi, discipline sau rubrici. Emite câte un record separat pentru fiecare zi. "
          "Pentru NOTE, forma fizică poate fi NOTĂ/ZI, cu luna indicată contextual în ACEEAȘI rubrică. Data este lizibilă numai dacă luna este demonstrabilă vizual acolo; "
          "nu deduce luna din perioada cerută și nu o împrumuta din altă rubrică. "
          "legible=true numai dacă TOATE câmpurile sunt citibile direct din fotografie, fără inferență. Nu ghici.")
        rows=_parse_vision_records(_vision_request(prompt,left,right),student_names,start)
        out=[]
        for r in rows:
            try:
                idx=int(r["student_index"]); kind=str(r["kind"]); date=normalize_ddmm(r["date"],start.year)
                conf=float(r.get("confidence",0)); val=str(r.get("value","")).strip()
                if not(0<=idx<len(student_names)) or kind not in {"grade","absence"} or not date_in_period(date,start,end):
                    continue
                if kind=="grade" and (not val.isdigit() or not 1<=int(val)<=10): continue
                legible=bool(r.get("legible",False))
                out.append(ImportProposal(idx,str(r["category"]).strip(),str(r["subject"]).strip(),kind,val,date,
                    bool(r.get("motivated",False)),conf,str(r.get("source_image","")),legible and conf>=0.90,""))
            except Exception:
                continue
        return out

    targets=[{"student_index":p.student_index,"category":p.category,"subject":p.subject,
              "kind":p.kind,"source_image":p.source_image} for p in items if not p.verifiable]
    second=read_pass(2,targets,complete=True)
    passes=[items,second]

    def consensus(pass_lists):
        votes={}
        examples={}
        for pass_items in pass_lists:
            seen=set()
            for p in pass_items:
                k=_semantic_key(p)
                if k in seen: continue
                seen.add(k); examples[k]=p
                if p.verifiable: votes[k]=votes.get(k,0)+1
        return votes,examples

    votes,examples=consensus(passes)
    unresolved=[p for k,p in examples.items() if votes.get(k,0)<2]
    if unresolved:
        third_targets=[{"student_index":p.student_index,"category":p.category,"subject":p.subject,
                        "kind":p.kind,"source_image":p.source_image}
                       for p in unresolved]
        third=read_pass(3,third_targets,complete=False)
        passes.append(third)
        votes,examples=consensus(passes)

    recovered=[]
    for k,p in examples.items():
        count=votes.get(k,0)
        if count>=2:
            recovered.append(ImportProposal(p.student_index,p.category,p.subject,p.kind,p.value,p.date,p.motivated,
                p.confidence,p.source_image,True,
                f"Demonstrat prin consensul a {count} citiri independente lizibile ale fotografiei originale."))
        else:
            recovered.append(ImportProposal(p.student_index,p.category,p.subject,p.kind,p.value,p.date,p.motivated,
                p.confidence,p.source_image,False,
                "Fără consens de minimum două citiri independente lizibile după epuizarea recuperării automate."))
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
        verified_semantics={(p.value if p.kind=="grade" else "",p.motivated) for p in rows if p.verifiable}
        if len(verified_semantics)==1:
            # Un singur rezultat a obținut consensul cerut; citirile izolate contradictorii nu îl anulează.
            wanted=next(iter(verified_semantics))
            candidates=[p for p in rows if p.verifiable and ((p.value if p.kind=="grade" else "",p.motivated)==wanted)]
            out.append(max(candidates,key=lambda p:p.confidence)); continue
        if len(verified_semantics)>1 or len(semantics)!=1:
            # Mai multe valori demonstrate contradictoriu, sau nicio valoare demonstrată: fail closed.
            best=max(rows,key=lambda p:p.confidence)
            out.append(ImportProposal(best.student_index,best.category,best.subject,best.kind,best.value,best.date,best.motivated,best.confidence,best.source_image,False,"Citiri contradictorii fără un singur rezultat demonstrat; nu se scrie automat."))
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
