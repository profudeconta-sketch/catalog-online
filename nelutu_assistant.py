"""Neluțu — asistent local, gratuit și strict read-only pentru Portalul Părinților."""
from __future__ import annotations
import re, unicodedata
import hashlib
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class NelutuAnswer:
    intent: str
    text: str
    source_label: str | None = None
    source_url: str | None = None
    serious: bool = False

LEGAL_SOURCES = {
    "lege_198": ("Legea învățământului preuniversitar nr. 198/2023 — Portal Legislativ", "https://legislatie.just.ro/Public/DetaliiDocument/277920"),
    "rofuip": ("ROFUIP — Ordinul nr. 5.726/2024, forma consolidată — Portal Legislativ", "https://legislatie.just.ro/Public/DetaliiDocumentAfis/301727"),
    "statut": ("Statutul elevului — Ordinul nr. 5.707/2024 — Ministerul Educației", "https://www.edu.ro/sites/default/files/_fi%C8%99iere/Legislatie/2024/OM_5707_2024_Statut_elev.pdf"),
}
QUICK_TOPICS=("Cum folosesc portalul?","Note și medii","Absențe și motivări","Învoire","Documente","Burse","Înștiințări de la școală","Drepturi și obligații","Cum funcționează Neluțu?")

def _norm(text:str)->str:
    text=unicodedata.normalize("NFKD",str(text or ""))
    text="".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+"," ",text).strip()

def _has_any(q:str, words:Iterable[str])->bool:
    return any(_norm(w) in q for w in words)

def _src(k:str):
    return LEGAL_SOURCES[k]

# Replici scurte, locale și deterministe: varietate fără AI extern și fără efecte secundare.
# Situațiile sensibile sunt excluse de apelant; aici condimentăm doar răspunsurile obișnuite.
_ARD_REMARKS = {
    "authorized_context": (
        "No, amu vorbim din ce-i scris, nu din ce-o visat clopu'. 😄",
        "Așe da: avem datele-n față și nu mai ghicim în zațu' de cafea. 🤠",
        "No, aici îi treabă limpede; cifrele n-au unde să fugă.",
        "Bun, am pus degetu' digital pă rându' care trăbă. 😄",
        "No, vezi? Când avem faptele, și Neluțu grăiește mai cu spor.",
    ),
    "portal_component": (
        "No, desfacem lucrurile pă rând, că nici slănina nu să taie cu toporu'. 😄",
        "Așe, am ajuns la sertaru' potrivit. Să vedem ce-i în el. 🤠",
        "No, nu-i bai: meniurile-s multe, da' Neluțu are răbdare cât o zi de post.",
        "Bun, aici nu ne grăbim; butonu' nu pleacă nicări fără noi. 😄",
        "No, tăt îi mai ușor când știi la ce poartă să bați.",
    ),
    "grades": (
        "No, notele-s ca vremea-n Apuseni: uneori îți plac, alteori îți iei sumanu'. 😄",
        "Așe, ne uităm la cifre fără să le speriem, că nu fug din catalog. 🤠",
        "No, media n-o înduplecăm cu povești; da' o putem lămuri omenește.",
        "Bun, punem socoteala pă masă și vedem de unde vine.",
    ),
    "documents": (
        "No, hârtiile-s multe, da' măcar astea digitale nu cad din dosar. 😄",
        "Așe, luăm actele pă rând; nu facem căpiță din PDF-uri. 🤠",
        "No, documentu' întâi îl verificăm și numa' după aia îi dăm drumu' la drum.",
        "Bun, aici Neluțu-i poștaș numa' cu gura; butonu' rămâne la tine. 😄",
    ),
    "leave": (
        "No, la învoire nu fugim înaintea aprobării, că nici căruța înaintea calului n-o punem. 😄",
        "Așe, cererea merge la poartă; aprobarea-i cheia, nu clanța. 🤠",
        "No, întâi starea, apoi plecarea. Altfel ne trezim cu Neluțu portar fără fluier.",
    ),
    "hello": (
        "No, servus! Clopu'-i pă cap, rotițele-s unse, putem începe. 🤠",
        "Servus! No, zi ce bai ai, că de stat degeaba pot și fără procesor. 😄",
        "No, bine-ai venit! Io-s aci; numa' adevăru' să-l cerem, că povești avem destule.",
        "Servus! Așe-mi place: omu' întreabă, Neluțu scormonește prin ce știe. 🤠",
    ),
    "fallback": (
        "No, aici m-ai prins cu un picior în ceață și unu-n opinci. 😄",
        "Așe întrebare... de-mi mai dai un fir, facem ghem din ea. 🤠",
        "No, n-o să mă dau rotund numa' ca să par pătrat de deștept. Mai zi-mi o țâră.",
        "Hmmm... aici clopu' nu-i antenă. Reformulează oleacă și ne prindem noi. 😄",
    ),
    "general": (
        "No, încet și bine, că graba strică și treaba digitală. 😄",
        "Așe, mergem pă fir; nu sărim gardu' până nu vedem ce-i dincolo. 🤠",
        "No, io am răbdare. Curentu' să nu să ia, că în rest ne descurcăm. 😄",
        "Bun. Întrebarea-i la noi, răspunsu' îl ținem cu picioarele pă pământ.",
        "No, dacă știm, spunem; dacă nu știm, nu scoatem iepuri din clop. 🤠",
    ),
}

def _ardelean_remark(question:str, intent:str)->str:
    choices=_ARD_REMARKS.get(intent) or _ARD_REMARKS["general"]
    seed=(str(intent)+"|"+_norm(question)).encode("utf-8")
    idx=int.from_bytes(hashlib.sha256(seed).digest()[:4],"big") % len(choices)
    return choices[idx]

def _with_remark(answer:NelutuAnswer, question:str)->NelutuAnswer:
    if answer.serious or answer.intent in {"safety","discipline","legal_general"}:
        return answer
    remark=_ardelean_remark(question, answer.intent)
    return NelutuAnswer(answer.intent, remark+"\n\n"+answer.text, answer.source_label, answer.source_url, answer.serious)

PORTAL_KNOWLEDGE = {
    "scoala": "Fila Școală conține comunicările și documentele trimise de școală. Un document nou rămâne neaccesat până la deschiderea lui din contul autentificat; WhatsApp este doar alertă și nu ține locul confirmării interne.",
    "invoire": "Fila Învoire arată solicitarea zilei curente, starea ei și, dacă este aprobată, biletul de voie. Cererea în așteptare nu este aprobare; biletul de voie nu motivează automat absențele.",
    "documente": "Fila Documente permite trimiterea și consultarea documentelor părinte→școală: dosar personal, scutiri medicale, dosar bursă și motivare absențe părinte.",
    "dosar personal": "Dosarul personal permite selectarea tipului de document, încărcarea PDF/JPG/JPEG/PNG și transmiterea către diriginte.",
    "scutiri medicale": "Zona Scutiri medicale este pentru documentele medicale transmise dirigintelui; documentul încărcat și transmiterea sunt operații distincte de simpla selectare a fișierului.",
    "dosar bursa": "Dosarul de bursă este împărțit în Merit, Socială–venit, Socială–orfan, Socială–medicală, Mame minore și CES. Neluțu explică interfața, nu decide eligibilitatea.",
    "motivare absente parinte": "Zona de motivare arată orele disponibile din plafon, persoana care transmite, elevul, adresa, numărul matricol, data absenței și numărul de ore. Previzualizarea PDF nu transmite cererea și nu consumă ore; transmiterea finală o înregistrează.",
    "documente deja transmise": "Lista documentelor deja transmise permite consultarea și descărcarea documentului înregistrat și, dacă este configurat, deschiderea manuală a WhatsApp către diriginte.",
    "note": "Situația școlară afișează note pe discipline/module și mediile calculate din datele disponibile. Neluțu poate explica valorile din contextul autorizat, dar nu le poate modifica.",
    "absente": "Pentru fiecare disciplină/modul portalul afișează totalul absențelor și separă nemotivatele de motivate. O absență este afișată conform stării existente în catalog; Neluțu nu inventează motivul unei stări dacă acesta nu este disponibil în context.",
    "medii": "Portalul calculează și afișează media culturii generale, media modulelor tehnologice și media generală din datele disponibile, plus poziția școlară calculată.",
    "purtare": "Portalul afișează nota la purtare disponibilă/calculată conform logicii aplicației. Neluțu o explică, dar nu o modifică și nu substituie decizia școlii unde este necesară.",
    "actualizeaza datele": "Butonul Actualizează Datele reîncarcă datele disponibile portalului; Neluțu nu îl apasă în locul părintelui.",
    "whatsapp": "Butoanele WhatsApp deschid un mesaj pregătit pentru trimitere manuală. WhatsApp nu înlocuiește notificarea sau confirmarea internă din portal.",
    "deschide documentul": "Butonul de deschidere a documentului școlii înregistrează accesarea conform fluxului portalului și permite apoi descărcarea documentului.",
    "previzualizare pdf": "Previzualizarea PDF permite verificarea cererii înainte de transmitere; nu este depunere și nu consumă plafonul.",
}

def portal_topics()->tuple[str,...]:
    return tuple(PORTAL_KNOWLEDGE)

def _context_lookup(q:str, context:dict|None):
    if not context:
        return None
    # Contextul este construit exclusiv din date deja autorizate pentru elevul autentificat.
    nq=_norm(q)
    for item in context.get("facts", ()):
        keys=tuple(item.get("keywords", ()))
        if keys and _has_any(nq, keys):
            return str(item.get("answer") or "").strip() or None
    return None

def build_student_context(*, media_generala=None, media_cultura=None, media_module=None,
                          purtare=None, total_absente=None, absente_nemotivate=None,
                          absente_motivate=None, discipline=None)->dict:
    """Construiește numai fapte deja calculate/autorizate de portal; nu citește și nu scrie stocare."""
    facts=[]
    def put(keys, text):
        facts.append({"keywords": tuple(keys), "answer": text})
    if media_generala is not None: put(("media generala","media mea"), f"Media generală afișată acum este {media_generala}.")
    if media_cultura is not None: put(("media cultura","cultura generala"), f"Media pentru cultura generală afișată este {media_cultura}.")
    if media_module is not None: put(("media module","module tehnologice"), f"Media modulelor tehnologice afișată este {media_module}.")
    if purtare is not None: put(("nota la purtare","purtare"), f"Nota la purtare afișată acum este {purtare}.")
    if total_absente is not None:
        put(("cate absente","total absente","absente am"), f"Portalul afișează {total_absente} absențe în total: {absente_nemotivate or 0} nemotivate și {absente_motivate or 0} motivate.")
    if absente_nemotivate is not None:
        put(("absente nemotivate","nemotivate"), f"Portalul afișează {absente_nemotivate} absențe nemotivate. Contextul arată starea, nu dovedește cauza individuală pentru care fiecare a rămas nemotivată.")
    if absente_motivate is not None: put(("absente motivate","motivate"), f"Portalul afișează {absente_motivate} absențe motivate.")
    for row in (discipline or ()):
        name=str(row.get("name") or "").strip()
        if not name: continue
        put((name,), f"La {name}, portalul afișează: note {row.get('notes','—')}; absențe {row.get('absences','—')}; media actuală {row.get('average','—')}.")
    return {"facts": facts}

def answer_with_context(question:str, context:dict|None=None)->NelutuAnswer:
    q=_norm(question)
    # Siguranța are prioritate absolută față de potrivirea cu o filă/componentă.
    safety = answer(question)
    if safety.intent == "safety":
        return safety
    contextual=_context_lookup(q, context)
    if contextual:
        return _with_remark(NelutuAnswer("authorized_context", "No, aici pot să mă uit la ce-ți arată chiar portalul tău. 😄 " + contextual + " Eu îți explic ce-i înregistrat; nu schimb nimic."), question)
    for topic, explanation in PORTAL_KNOWLEDGE.items():
        if _has_any(q, (topic,)):
            return _with_remark(NelutuAnswer("portal_component", "No binie mă. 😄 " + explanation + " Dacă-mi spui ce anume vezi acolo, îl desfacem fir cu fir; io am vreme, rotițele n-au autobuz de prins. 😂"), question)
    return answer(question)

def answer(question:str)->NelutuAnswer:
    q=_norm(question)
    if not q:
        return NelutuAnswer("empty","No, amu m-ai prins cu traista goală. 😄 Scrie-mi ce vrei să afli și-mi pun rotițele la lucru. N-or fi ele de moară, da' se-nvârt. 😂")

    # Pericol/situații sensibile: Neluțu rămâne empatic, iar poanta se dă singură mai încet.
    if _has_any(q,("violenta","lovit","batut","bataie","bullying","hartuit","abuz","amenintat","amenintare","sinucidere","autovatam","drog","agresiune","pericol")):
        return NelutuAnswer("safety","Îmi pare rău că e vorba despre o situație serioasă. Aici Neluțu pune glumele în cui. Dacă există pericol imediat, cere ajutor serviciilor de urgență. Pentru o situație școlară, anunță cât mai repede dirigintele și conducerea școlii. Eu pot explica portalul și regulile generale, dar nu pot investiga cazul și nu pot înlocui un specialist.",serious=True)

    if _has_any(q,("cum functioneaza nelutu","ce poti face","ce stii sa faci","esti ai","inteligenta artificiala")):
        return NelutuAnswer("about","Ie mă. 😄 Eu-s Neluțu, ajutor local al portalului. Nu-s vreun balaur cu inteligență artificială plătită: răspund dintr-o bază controlată de informații și reguli. Nu citesc secrete, nu schimb catalogul, nu trimit acte și nu aprob nimic. Pe scurt: am gură digitală, da' mâinile le țin în buzunar. 😂")

    if _has_any(q,("cum folosesc portalul","portal","meniu","unde gasesc","cum functioneaza")):
        return NelutuAnswer("portal","Ie mă! Portalul îi mai cuminte decât pare. 😄 După autentificare ai trei zone mari: „Școală” pentru comunicările primite, „Învoire” pentru cereri și „Documente” pentru ce trimiți dirigintelui. Mai jos vezi situația școlară. Spune-mi ce vrei să faci și te duc până la buton; nu-l apăs eu, că n-am degete, numa' păreri. 😂")

    if _has_any(q,("pin","autentific","logare","matricol","nu pot intra")):
        return NelutuAnswer("login","No binie mă, la poarta digitală ne trebuie numărul matricol și PIN-ul corect. 😄 Verifică exact ce-ai introdus; dacă tot nu merge, contactează dirigintele. Neluțu nu vede, nu schimbă și nu recuperează PIN-uri. Api dacă le-aș ști pe toate, ar trebui să-mi pun singur lacăt. 😂")

    if _has_any(q,("nota","note","medie","medii","clasament","situatia scolara")):
        return NelutuAnswer("grades","Aha, no, aici intrăm în ograda notelor. 😄 Portalul afișează notele, mediile și indicatorii situației școlare disponibili. Eu îți explic ce vezi, dar nu pot pune, șterge ori modifica vreo notă. Pentru o neconcordanță concretă, vorbește cu profesorul sau dirigintele — eu îs bun la lămurit, nu la umblat cu pixul prin catalog. 😂")

    if _has_any(q,("absenta","absente","motivare","motivez","scutire")):
        l,u=_src("rofuip")
        return NelutuAnswer("absences","No, amu cu absențele să fim preciși, că ele n-au simțul umorului. 😄 ROFUIP prevede, pentru cererea scrisă a părintelui/reprezentantului legal ori a elevului major, limita de 40 de ore de curs într-un an școlar, fără a depăși 20% din orele unei discipline; cererea este adresată cadrului competent și avizată în prealabil de director. Actele justificative au reguli și termene proprii. Portalul doar ajută transmiterea; aplicarea motivării aparține școlii potrivit cadrului legal. Api eu pot număra orele, da' director încă nu m-or făcut. 😂",l,u)

    if _has_any(q,("invoire","plecare","plece","iesire","parasirea scolii")):
        return NelutuAnswer("leave","Ie mă. 😄 În fila „Învoire” completezi solicitarea disponibilă și, după transmitere, urmărești starea ei. Elevul nu trebuie să considere simpla cerere drept aprobare. Neluțu nu aprobă și nu refuză învoiri — eu îs portar numa' la vorbe. 😂 Pentru urgențe sau neclarități, contactează dirigintele.")

    if _has_any(q,("document","incarc","pdf","dosar","medical","adeverinta")):
        return NelutuAnswer("documents","No binie mă, „Documente” îi mica noastră poștă fără timbre. 😄 Alegi categoria, atașezi documentul și folosești butonul de transmitere. Când portalul confirmă transmiterea, solicitarea intră în fluxul către diriginte conform mecanismului aplicației. Eu nu pot încărca ori trimite în locul tău — că după aia mă trezesc și secretar, și poștaș, și fără spor de vechime. 😂")

    if _has_any(q,("bursa","burse","merit","sociala","ces","orfan","venit")):
        return NelutuAnswer("scholarship","Aha, no, la burse alegem categoria potrivită din zona de documente și încărcăm actele cerute. 😄 Eu pot explica interfața, dar nu stabilesc eligibilitatea și nu aprob bursa. Pentru condițiile aplicabile cazului concret, verifică informația oficială a școlii/secretariatului. N-aș vrea să promit bani cu buzunarele mele digitale goale. 😂")

    if _has_any(q,("instiintare","notificare","comunicare","citit","confirmare","confirmat")):
        return NelutuAnswer("school_notice","No, aici mecanismul îi făcut să nu joace alba-neagra cu „citit/necitit”. 😄 În aplicația noastră, documentul școlii este înregistrat ca accesat când este deschis din contul autentificat și se execută confirmarea prevăzută de portal; simplul mesaj WhatsApp nu este acea confirmare internă. WhatsApp îi clopoțelul de la poartă, portalul îi registrul. 😂")

    if _has_any(q,("whatsapp","wapp","mesaj")):
        return NelutuAnswer("whatsapp","Ie mă. 😄 Butonul WhatsApp doar pregătește mesajul; trimiterea o faci tu manual. Confirmările portalului rămân în sistemul autentificat. Eu îți pun plicul în mână, da' nu fug cu el până la destinatar — n-am nici picioare, și nici abonament de autobuz. 😂")

    if _has_any(q,("purtare","sanctiune","sanctiuni","disciplin","contestatie")):
        l,u=_src("statut")
        return NelutuAnswer("discipline","No, amu îi treabă serioasă. Statutul elevului reglementează drepturi, îndatoriri și sancțiuni. Eu pot explica regula generală și sursa, dar nu stabilesc dacă o sancțiune este justificată într-un caz concret și nu înlocuiesc procedura școlii ori o contestație. Aici îmi țin clopul pe cap și competențele în buzunar. 😄 Pentru cazul concret: diriginte, conducerea școlii și, dacă este necesar, specialistul competent.",l,u,True)

    if _has_any(q,("drept","obligatie","lege","legal","regulament","statut")):
        l,u=_src("lege_198")
        return NelutuAnswer("legal_general","No, amu intrăm pe teren juridic și Neluțu își îndreaptă clopul. 😄 Pot explica reguli generale din surse oficiale și îți arăt baza folosită, dar nu inventez articole și nu dau verdicte pentru cazuri individuale. Pentru o decizie, contestație ori interpretare aplicată situației tale, discută cu dirigintele, conducerea școlii sau specialistul competent. Eu am clop, nu robă pe USB. 😂 Spune-mi tema exactă.",l,u)

    if _has_any(q,("salut","buna","servus","ceau","cine esti","nelutu")):
        return NelutuAnswer("hello","Ie mă, servus! Eu-s Neluțu. 😄 Mocan digital de pe Valea Arieșului: iute la minte, molcom la vorbă și cu rotițele unse cât să nu scârțâie prin portal. 😂 Nu mă supăr, nu judec și nu modific nimic în catalog. Întreabă-mă; dacă nu știu, îți spun. Îi mai sănătos decât să scot adevărul din clop.")

    return _with_remark(NelutuAnswer("fallback","No, amu m-ai băgat oleacă-n ceață. 😄 Nu vreau să scot un răspuns din clop doar ca să par deștept. Spune-mi altfel sau alege o temă: portal, note, absențe, învoire, documente, burse, înștiințări ori drepturi. Dacă-i un caz pe care nu-l pot lămuri sigur, te trimit la omul competent — mai bine Neluțu prudent decât Neluțu morișcă. 😂"), question)

# Contract invariabil: doctor în portal, dar cu caracterul lui Neluțu și cu mâinile în buzunar.
EXPERT_CONTRACT = {
    "scope": "portal_parent_authenticated_context_only",
    "read_only": True,
    "never_invent": True,
    "never_judge": True,
    "infinite_patience": True,
    "self_ironic_humor": True,
    "regional_voice": "Valea Ariesului, grai de mocan; iute la minte, molcom la vorba",
    "serious_topics_suppress_playful_humor": True,
    "no_cross_student_access": True,
    "no_secret_access": True,
    "no_paid_or_external_ai": True,
}

def expert_contract()->dict:
    return dict(EXPERT_CONTRACT)

def read_only_contract()->dict:
    return {"writes_primary_data":False,"writes_files":False,"calls_paid_ai":False,"calls_external_ai":False,"can_change_grades":False,"can_send_documents":False,"can_approve_requests":False,"reads_secrets":False,"reads_student_records":False}
