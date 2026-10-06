"""Tutorial local și router tolerant pentru Neluțu — fără I/O, fără rețea, fără scrieri."""
from __future__ import annotations
import re, unicodedata
from nelutu_assistant import NelutuAnswer, answer_with_context as _base_answer

TUTORIAL_TOPIC="Tutorial complet — Portalul Părinților"
TUTORIAL_TEXT="""No, hai să-ți arăt tătă aplicația, fără drumuri degeaba. 🤠

**🔔 Școală — ce vine de la școală la tine**
Aici găsești înștiințările și documentele trimise prin diriginte. Un document nou rămâne neaccesat până îl deschizi din contul autentificat. Când folosești „Deschide documentul și confirmă luarea la cunoștință”, portalul înregistrează accesarea. WhatsApp poate fi alerta; evidența sigură rămâne în portal.

**🚪 Învoire — solicitarea pentru ziua curentă**
Alegi ora viitoare și motivul, apoi transmiți. „În așteptare” nu înseamnă aprobat. După aprobarea dirigintelui apare biletul de voie. Biletul nu este motivare/scutire și nu modifică automat absențele.

**📁 Documente — părinte → diriginte/școală**
Alegi categoria și tipul actului, încarci PDF/JPG/JPEG/PNG și apeși transmiterea. Numai confirmarea de succes înseamnă că documentul a fost salvat și înregistrat. În „Documente deja transmise dirigintelui” verifici ce ai trimis.

• **Dosar personal:** actele pentru dosarul elevului.
• **Scutiri medicale:** încarci scutirea și o transmiți dirigintelui.
• **Dosar bursă:** alegi tipul bursei și documentului; portalul transmite actele, iar eligibilitatea este stabilită de școală conform regulilor aplicabile.
• **Motivare absențe părinte:** completezi formularul; previzualizarea PDF este doar pentru verificare. Abia „Generează, salvează și trimite” face transmiterea. Când portalul confirmă că cererea este transmisă și considerată depusă, nu mai trebuie să aduci la școală aceeași cerere tipărită.

**📊 Situația școlară**
Vezi notele, mediile, absențele, purtarea și indicatorii disponibili. Eu explic ce vezi, dar nu modific nimic.

**De ce-i util?** Pentru fluxurile pe care sistemul le confirmă ca transmise/depuse, ai înregistrarea în cont și scapi de drumuri făcute doar ca să predai aceeași hârtie. Comunicarea este organizată prin diriginte și fluxurile școlii. Portalul nu inventează aprobarea directorului și nu transformă automat orice încărcare într-o decizie a conducerii.

Nu trebuie să știi denumirile din meniu. Poți să-mi zici „unde bag scutirea?”, „cum trimit hârtia la dirigu?”, „unde văd ce-o trimis școala?” ori „mai trebe să duc cererea pe hârtie?” și te îndrum. 😄"""

def _norm(text):
    text=unicodedata.normalize("NFKD",str(text or ""))
    text="".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+"," ",text).strip()

ALIASES={
"tutorial":("tutorial","ghid","arata mi aplicatia","explica mi aplicatia","cum folosesc tot","cum merge tot"),
"school":("unde vad ce o trimis scoala","ce a trimis scoala","instiintare","mesaj de la scoala"),
"medical":("unde bag scutirea","scutire medicala","adeverinta medicala","trimit scutirea"),
"documents":("trimit hartia","trimit actul","trimit la dirigu","incarc document","unde incarc"),
"excuse":("motivez absente","motivare absente","mai trebe sa duc","mai trebuie sa duc","cererea pe hartie","cererea tiparita"),
"leave":("invoire","iau copilul","plece de la scoala","cer voie"),
"sent":("ce am trimis","s a trimis","document transmis","cum stiu ca am trimis"),
}
def _match(q):
    nq=_norm(q)
    for intent,phrases in ALIASES.items():
        if any(_norm(p) in nq for p in phrases): return intent
    return None

def answer_parent(question,context=None):
    intent=_match(question)
    if intent=="tutorial":
        return NelutuAnswer("portal_tutorial",TUTORIAL_TEXT)
    guides={
      "school":"No, mergi la **🔔 Școală**. Acolo vezi ce a transmis școala prin diriginte. Deschiderea documentului din cont înregistrează luarea la cunoștință conform fluxului portalului. 🤠",
      "medical":"No, mergi la **📁 Documente → 🏥 Scutiri medicale**. Alegi tipul, încarci fișierul și apeși transmiterea. Te oprești abia când portalul confirmă că documentul a fost salvat și înregistrat. 🤠",
      "documents":"No, **📁 Documente** îi poșta digitală. Alegi Dosar personal, Scutiri medicale, Dosar bursă ori Motivare absențe, încarci/completezi și transmiți. Confirmarea verde este reperul că operația a reușit. 🤠",
      "excuse":"No, pentru cererea părintelui mergi la **📁 Documente → 📝 Motivare absențe părinte**. Previzualizarea nu transmite nimic. După „Generează, salvează și trimite”, dacă portalul confirmă că cererea este transmisă și considerată depusă, **nu mai trebuie să aduci la școală aceeași cerere tipărită**. 🤠",
      "leave":"No, mergi la **🚪 Învoire**. Completezi cererea pentru ziua curentă și urmărești starea. Cererea în așteptare nu este aprobare; după aprobarea dirigintelui apare biletul de voie. 🤠",
      "sent":"No, în **📁 Documente → Documente deja transmise dirigintelui** verifici ce a fost înregistrat. Nu confundăm selectarea ori previzualizarea cu transmiterea confirmată. 🤠",
    }
    if intent in guides: return NelutuAnswer("parent_guide_"+intent,guides[intent])
    return _base_answer(question,context)

def contract():
    return {"writes_data":False,"uses_network":False,"external_ai":False,"changes_school_workflow":False}
