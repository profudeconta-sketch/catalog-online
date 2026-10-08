"""Îndrumări suplimentare pentru portal, numai citire, fără acțiuni."""
from __future__ import annotations
import difflib
import re
import unicodedata
from nelutu_assistant import NelutuAnswer

def _norm(s):
    s=unicodedata.normalize("NFKD",str(s or ""))
    s="".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+"," ",s).strip()

# Pași verificați în fluxurile portalului; nu pretindem că am efectuat operații.
FAQ={
 "login":(("nu pot sa intru","nu ma pot autentifica","am uitat pinul","pin gresit","nu merge logarea"),
  "No, verifică întâi **numărul matricol** și **PIN-ul**, fără să mi le trimiți mie. Dacă autentificarea e refuzată, contactează dirigintele. Eu nu văd, nu recuperez și nu schimb codurile."),
 "medical":(("cum trimit scutirea medicala","unde incarc adeverinta medicala","scutire pentru copil"),
  "No, intră în **Documente → Scutiri medicale**. 1. Alege categoria. 2. Atașează documentul. 3. Verifică datele. 4. Apasă butonul de transmitere. 5. Așteaptă confirmarea în portal. Simplul atașament nu înseamnă trimitere."),
 "excuse":(("cum motivez absentele","cum trimit motivarea","cerere pentru absente","motivare parinte"),
  "No, mergi la **Documente → Motivare absențe părinte**. 1. Completează solicitarea. 2. Verifică previzualizarea. 3. Folosește **Generează, salvează și trimite**. 4. Așteaptă confirmarea depunerii. Previzualizarea singură nu trimite nimic."),
 "leave":(("cum cer invoire","cum solicit invoire","bilet de voie","pleaca mai devreme"),
  "No, în **Învoire**: 1. Deschide cererea pentru **ziua curentă**. 2. Selectează motivul și ora permisă. 3. Trimite solicitarea. 4. Urmărește starea. **În așteptare nu înseamnă aprobată**. Biletul apare după aprobarea dirigintelui; dacă ora trece fără aprobare, solicitarea poate expira."),
 "notice":(("cum confirm instiintarea","unde vad instiintarile","am primit notificare","cum citesc mesajul scolii"),
  "No, deschide **Școală**. 1. Identifică înștiințarea nouă. 2. Deschide documentul în contul autentificat. 3. Folosește confirmarea prevăzută de portal. WhatsApp anunță, dar nu ține locul confirmării interne."),
 "sent":(("cum verific daca am trimis","unde vad documentele trimise","a ajuns documentul","cum stiu ca a fost depus"),
  "No, verifică **Documente → Documente deja transmise dirigintelui**. Caută confirmarea înregistrării. Dacă ai doar fișierul selectat sau previzualizarea, încă nu-i dovadă de transmitere."),
 "whatsapp":(("whatsapp nu trimite","cum trimit pe whatsapp","mesaj whatsapp","notificare whatsapp"),
  "No, butonul WhatsApp poate pregăti mesajul, dar **trimiterea o confirmi tu în WhatsApp**. O notificare WhatsApp nu înlocuiește transmiterea documentului în portal.")
}

def _phrase(q,p):
    return bool(re.search(r"(?<![a-z0-9])"+re.escape(p)+r"(?![a-z0-9])",q))

def answer_portal(question):
    q=_norm(question)
    if not q:
        return None
    hits=[]
    for key,(phrases,_) in FAQ.items():
        for phrase in phrases:
            p=_norm(phrase)
            if _phrase(q,p):
                hits.append((len(p.split()),len(p),key))
    if hits:
        key=max(hits)[2]
        return NelutuAnswer("portal_faq_"+key,FAQ[key][1])
    # Toleranță conservatoare doar pentru un termen lung, fără aproximări riscante.
    tokens=q.split()
    typo_map={"invoire":"leave","scutire":"medical","instiintare":"notice","whatsapp":"whatsapp"}
    for token in tokens:
        if len(token)<7:
            continue
        matches=difflib.get_close_matches(token,tuple(typo_map),n=1,cutoff=0.88)
        if matches and (len(tokens)<=7):
            key=typo_map[matches[0]]
            return NelutuAnswer("portal_faq_"+key,FAQ[key][1])
    return None

def contract():
    return {"writes_data":False,"uses_network":False,"calls_paid_ai":False}
