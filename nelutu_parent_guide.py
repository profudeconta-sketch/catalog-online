"""Tutorial local și router tolerant pentru Neluțu — fără I/O, fără rețea, fără scrieri."""
from __future__ import annotations
import re, unicodedata
from nelutu_assistant import NelutuAnswer, answer_with_context as _base_answer

TUTORIAL_TOPIC="Tutorial complet — Portalul Părinților"
TUTORIAL_TEXT="""# 🤠 No, io-s Neluțu. Hai să-ți arăt tăt sistemu’, cap-coadă.

**Întâi să ne cunoaștem.** Io-s **Neluțu — PRIMU’ AI DIN ARDEAL, NELUȚU-AL NOST**. M-o făcut omu’ ăsta ca să nu trebuiască părintele să umble prin aplicație ca prin pădure după bureți și nici dirigintele să repete de cincizeci de ori aceeași explicație. Îs un ajutor local al sistemului: cunosc cum îi așezată aplicația, pot explica fluxurile și pot răspunde la întrebări, da’ **nu scriu note, nu șterg absențe, nu aprob învoiri, nu trimit documente în locul tău și nu mă bag în datele altui elev**. Cu alte cuvinte, îs sfătos, nu primar. 😄

Am fost creat ca să fac sistemul mai ușor de înțeles pentru oameni, nu ca să înlocuiesc profesorul, părintele ori regulile școlii. Când îi vorba de butoane și drumuri prin portal, pot glumi. Când îi vorba de situația școlară, documente, disciplină ori legislație, las gluma mai încet și spun numai ce poate fi susținut de datele autorizate și de surse serioase. Bârfa-i bârfă, da’ munca-i muncă. 🤠

---

## 1. 🏠 Ce-i, de fapt, sistemul ăsta?

Sistemul are două fețe care lucrează împreună:

**Portalul Părinților** îi locul unde părintele/reprezentantul legal vede situația elevului și comunicările școlii, trimite documente și solicitări și urmărește ce s-o înregistrat.

**Catalogul Profesorilor/Dirigintelui** îi partea de lucru a școlii: note, absențe, motivări, documente, gestiunea elevilor, rapoarte, purtare, catalog oficial, importuri și închiderea situației școlare.

Între ele circulă informația controlat. Nu-i principiul „am apăsat ceva și Dumnezeu cu mila”. Sistemul încearcă să confirme ce s-o transmis, ce s-o accesat și ce stare are fiecare flux. Și unde operația-i sensibilă, verifică înainte să scrie. Așe-i bine: și la sarmale verifici oala înainte s-o răstorni. 😄

---

# 👨‍👩‍👧‍👦 PARTEA I — PORTALUL PĂRINȚILOR

## 2. 🔐 Intrarea în portal

Părintele intră cu datele de autentificare ale elevului. Portalul identifică elevul și afișează numai situația asociată contului autentificat. Datele reale de autentificare nu trebuie precompletate în formular.

Există și o cale separată pentru diriginte, destinată verificării portalului. Ea nu schimbă autentificarea părintelui. Neluțu, oricât l-ai gâdila, nu-ți spune parole și nu caută secrete. Aici îi mai încăpățânat decât o vacă la poarta nouă. 😄

După autentificare, părintele ajunge la fișa elevului și la cele trei zone mari: **🔔 Școală**, **🚪 Învoire** și **📁 Documente**. Pe lângă acestea, portalul afișează situația școlară disponibilă: note, medii, absențe, purtare și indicatorii calculați din catalog.

---

## 3. 🔔 Școală — ce vine de la școală spre părinte

Aici ajung înștiințările și documentele transmise prin diriginte. Un document nou este marcat ca nou/neaccesat până când părintele îl deschide din contul autentificat.

Când părintele folosește **„Deschide documentul și confirmă luarea la cunoștință”**, sistemul înregistrează prima accesare, cu data și ora, iar această stare poate fi văzută și de diriginte. Asta înseamnă că școala poate vedea diferența dintre „document trimis” și „document accesat de părinte”.

Documentul poate fi apoi descărcat. WhatsApp poate fi folosit ca alertă sau cale rapidă spre portal, dar evidența sigură a fluxului rămâne în sistem.

Pe românește: dacă telefonul zice „pling!”, aia-i soneria. Registrul îi în portal. 😄

---

## 4. 🚪 Învoire — când elevul trebuie să plece în ziua curentă

Învoirea este inițiată de părinte pentru **ziua curentă**. Părintele alege o oră viitoare și motivul disponibil în formular, apoi transmite solicitarea.

Solicitarea poate avea stări clare. **„În așteptare” nu înseamnă „aprobată”**. Dirigintele o verifică, iar după aprobare apare biletul de voie. Dacă ora solicitată trece fără aprobare, cererea poate deveni expirată/considerată refuzată conform fluxului implementat.

Există protecții ca să nu avem mai multe solicitări active pentru aceeași zi. Înainte de aprobare, cererea poate fi reformulată, iar sistemul lucrează cu ultima versiune relevantă.

Foarte important: **biletul de voie nu este motivare sau scutire și nu modifică automat absențele**. Dacă din plecare rezultă absențe, ele urmează regulile lor de evidență și motivare.

Deci biletul zice „poate pleca”, nu „s-o șters catalogul cu buretele”. Nici Neluțu n-are burete așe de mare. 😄

---

## 5. 📁 Documente — poșta digitală părinte → școală

Aici părintele trimite documente către diriginte/școală. Sistemul acceptă tipurile de fișiere prevăzute în interfață și validează documentul înainte de înregistrare.

Regula simplă: **selectarea fișierului nu înseamnă transmitere**. Nici previzualizarea nu înseamnă transmitere. Operația este considerată reușită numai când portalul afișează confirmarea că documentul a fost salvat și înregistrat.

După transmitere, în zona **„Documente deja transmise dirigintelui”** părintele poate verifica documentele înregistrate și le poate redeschide/descărca.

### 📂 Dosar personal
Aici intră documentele prevăzute pentru dosarul elevului: acte de identitate, certificat de naștere, dovezi și alte documente din categoriile disponibile.

### 🏥 Scutiri medicale
Părintele încarcă scutirea medicală și o transmite dirigintelui. Documentul este identificat și înregistrat controlat, astfel încât fluxul să nu se bazeze pe „parcă l-am trimis”.

### 🎓 Dosar bursă
Aici sunt organizate documentele pentru tipurile de bursă disponibile: cereri, acorduri, declarații, documente medicale și alte acte justificative prevăzute. Portalul **transmite și organizează documentele**; nu inventează eligibilitatea și nu se substituie deciziei școlii.

### 📝 Motivare absențe părinte
Părintele completează datele cererii. Poate genera o previzualizare pentru verificare, dar previzualizarea nu transmite nimic. Abia acțiunea **„Generează, salvează și trimite”** înregistrează cererea.

Pentru acest flux există evidența limitei anuale de ore gestionate prin cererea părintelui. Sistemul verifică utilizarea și blochează depășirea regulii implementate. După transmiterea reușită, portalul spune clar că cererea este transmisă și considerată depusă; nu mai este necesar să fie adusă la școală aceeași cerere tipărită. Dacă există o problemă de fond, dirigintele poate lua legătura separat cu părintele.

No, aici hârtia nu mai face turism până la școală dacă sistemul o confirmat depusă. Destul turism avem în denumirea clasei. 😄

---

## 6. 📊 Situația școlară văzută de părinte

Portalul citește catalogul și prezintă situația elevului: note, medii, absențe și informațiile de purtare disponibile. Este o fereastră de consultare pentru părinte; nu-i locul în care părintele schimbă catalogul.

Dacă elevul are o stare specială păstrată în sistem, istoricul relevant rămâne pentru consultare conform evidenței existente.

Neluțu poate explica ce înseamnă rubricile pe care le vezi. Nu inventează note lipsă, nu ghicește motivele unei absențe și nu compară pe ascuns elevul cu alt elev.

---

# 🧑‍🏫 PARTEA II — APLICAȚIA PROFESORULUI / DIRIGINTELUI

## 7. 🔐 Intrarea profesorului și sursa de date

Aplicația profesorului este zona de lucru. Catalogul Excel și registrele auxiliare sunt sincronizate și validate înaintea operațiilor importante. Identitatea elevului este verificată între foile obligatorii și evidența de gestiune.

Aici regula îi sănătoasă: dacă structura nu-i cea așteptată, sistemul preferă să oprească operația decât să scrie unde nu trebuie. Mai bine zice „nu” calculatorul decât să zică profesorul după două zile „no, unde mi-s datele?”. 😄

---

## 8. 🔔 Inbox-ul dirigintelui

Inbox-ul adună comunicările care cer atenția dirigintelui, inclusiv documentele trimise de părinți și solicitările de învoire. Elementele necitite sunt evidențiate, iar deschiderea lor poate marca notificarea ca citită conform fluxului.

Aici se vede legătura directă cu Portalul Părinților: părintele trimite, sistemul înregistrează, dirigintelui îi apare în Inbox. Nu trebuie să ghicească nimeni dacă porumbelul voiajor o ajuns. 😄

---

## 9. 📝 Notele

Profesorul poate selecta elevul, categoria — cultură generală sau module tehnologice — și disciplina/modulul, apoi introduce nota în sloturile prevăzute de catalog.

Sistemul lucrează cu structura catalogului și face validări înainte de salvare și sincronizare. Notele nu trebuie dublate arbitrar, iar operațiile sensibile sunt legate de elevul și disciplina selectate.

După actualizare, situația poate fi recalculată și reflectată în fișa elevului și în centralizatoare.

---

## 10. 📅 Absențele și motivarea lor

Profesorul poate adăuga o absență pentru elevul și disciplina/modulul selectate, în sloturile dedicate. Există și flux separat pentru **motivarea unei absențe existente**.

Asta-i important: motivarea nu înseamnă că absența n-o existat; înseamnă că starea ei se schimbă conform operației făcute în catalog.

Există și o zonă controlată pentru ștergerea unei note sau absențe introduse. Sistemul cere selectarea explicită a elementului. Operațiile astea nu-s pentru joacă; aici Neluțu își pune pălăria drept și nu mai spune bancuri până nu terminăm. 🤠

---

## 11. 📊 Fișa elevului și rezumatul

Dirigintele poate selecta elevul și vedea fișa/rezumatul școlar. Din această zonă poate genera documentele/rapoartele disponibile, inclusiv fișa PDF.

Actualizarea situației școlare poate genera și o comunicare către părinte, astfel încât părintele să știe că situația din Catalog Online a fost verificată/actualizată și să intre în portal pentru detalii.

---

## 12. 📈 Centralizatoare, statistici și rapoarte

Aplicația nu ține datele numai ca să se uite la ele. Poate construi centralizatoare și rapoarte pentru clasă: situația școlară, premii/ierarhii unde sunt calculate, absențe, indicatori de clasă și rapoarte sintetice ale dirigintelui.

Există exporturi pentru absențe lunare pe elevi și pe discipline/module, centralizări ale absențelor și clasamente după criteriile disponibile. Sunt disponibile și documente PDF/Excel pentru zonele implementate.

Pe scurt: dacă vrei să numeri absențele cu creionul, poți. Da’ Neluțu n-o să înțeleagă de ce te pedepsești singur. 😄

---

## 13. 🔐 Codurile PIN pentru părinți

Aplicația profesorului poate genera/descărca evidența codurilor PIN confidențiale pentru accesul părinților, conform funcției existente. Aceste date sunt sensibile.

Neluțu nu le afișează în conversație și nu le caută pentru curioși. La parole și PIN-uri, io-s mut ca peștele. 🤐

---

## 14. 👥 Gestiunea elevilor

Există o zonă dedicată datelor elevilor, părinților și situațiilor speciale. Sistemul verifică legătura dintre evidența JSON și catalogul Excel înainte de operații structurale.

Sunt prevăzute operații pentru consultare/editare, adăugarea unui elev și actualizarea stării școlare, cu validări. Pentru operații structurale există protecții tocmai fiindcă un elev nu-i un rând oarecare într-un tabel.

Elevii cu situații precum transfer/retragere pot rămâne în evidență cu istoricul necesar, în loc ca trecutul lor școlar să dispară ca și cum n-ar fi existat.

---

## 15. 📁 Centrul de documente al dirigintelui

Aici profesorul vede documentele asociate elevilor și comunicarea documentară cu părinții.

Pentru documentele venite de la părinte, dirigintele poate identifica și deschide documentul înregistrat. Pentru comunicările școală → părinte, dirigintele poate încărca/transmite documente și poate vedea dacă părintele le-a accesat.

La înștiințările școlii, starea trece practic din **neaccesat** în **accesat de părinte**, cu evidența momentului primei accesări. Confirmarea poate fi descărcată în fluxul disponibil.

Tot aici pot fi consultate scutirile/motivările întocmite de părinte. Cererea părintelui considerată depusă nu este transformată pe ascuns într-o altă decizie administrativă; sistemul păstrează rolurile separate.

---

## 16. 🚪 Legătura învoirii cu dirigintele

Cererea de învoire transmisă din Portalul Părinților ajunge în zona de lucru a dirigintelui. Dirigintele o verifică și decide asupra aprobării conform fluxului implementat.

După aprobare, părintele vede starea și biletul de voie. Dacă nu este aprobată la timp, sistemul nu pretinde că aprobarea ar exista.

Așe-i cinstit: „în așteptare” îi în așteptare. Nici dacă te uiți urât la ecran nu se transformă singură în „aprobat”. 😄

---

## 17. 🧭 Purtarea pe intervalele de cursuri

Purtarea este organizată pe intervalele de cursuri definite pentru anul școlar. Dirigintele acordă nota pentru fiecare interval, iar registrul dedicat este sincronizat separat.

Absențele nu inventează automat nota fiecărui interval. La închiderea anuală, regulile de nefrecventare și eventualele măsuri disciplinare sunt tratate în calculul și validarea anuală conform mecanismului implementat.

Lipsa notelor de purtare necesare poate bloca închiderea situației anuale. Și bine face: nu închidem anul cu jumătate de catalog și jumătate de speranță. 😄

---

## 18. 📷 Importul din catalogul fizic

Aplicația are o zonă pentru importul notelor și absențelor din fotografii ale catalogului fizic, pe o perioadă selectată.

Fluxul este construit prudent: imaginile din arhivă sunt validate și împerecheate, propunerile sunt comparate cu catalogul existent, iar suprapunerile nu trebuie duplicate. Înregistrările care nu pot fi demonstrate sigur nu trebuie scrise.

Înainte de actualizarea catalogului există confirmare, iar procesul include protecții și verificări post-scriere; dacă verificarea sau sincronizarea sigură eșuează, mecanismul poate restaura backupul conform implementării.

Aici deviza îi simplă: **nu băgăm în catalog ce nu putem demonstra că-i adevărat și lizibil**. Nici dacă poza seamănă cu Mona Lisa după ploaie. 😄

---

## 19. 📘 Catalogul oficial „la zi”

Dirigintele poate genera **catalogul oficial la zi** în format PDF. Această generare este separată de închiderea anuală și este **read-only**: citește situația existentă și produce documentul fără să modifice datele catalogului.

Este util pentru o reprezentare oficială a situației curente, dar nu înseamnă că anul școlar a fost închis.

---

## 20. 🔎 Validarea clasei înainte de închiderea anuală

Înainte de închiderea situației școlare, aplicația poate verifica întreaga clasă. Citește catalogul și registrele necesare și arată dacă elevii sunt pregătiți sau dacă există blocaje/date incomplete.

Validarea nu modifică Excelul, registrul de purtare ori gestiunea elevilor. Este diagnosticul de dinaintea operației finale.

Dacă lipsește ceva, sistemul spune. Nu merge pe principiul „las’ că poate nu observă nimeni”. Neluțu observă. 🤠

---

## 21. 🔒 Închiderea situației școlare și snapshoturile

Închiderea anuală este una dintre cele mai protejate operații. Ea nu trebuie confundată cu o simplă recalculare sau cu generarea PDF-ului „la zi”.

La închidere, situația validată este fixată în **snapshoturi anuale păstrate într-un registru privat separat**. Persistența este protejată împotriva suprascrierii unei închideri deja existente, iar conflictele trebuie să blocheze operația în loc să distrugă o stare anterioară.

Datele primare din catalog nu sunt modificate doar pentru faptul că s-a creat snapshotul de închidere. Operația fixează situația validată în registrul dedicat.

După ce setul necesar este complet, catalogul PDF al situației închise poate fi generat folosind snapshoturile validate.

Aici regula de aur nu-i poezie, îi centură de siguranță: **zero pierderi de date, zero pierderi de funcționalități, nicio suprascriere necontrolată**.

---

## 22. 🏁 Situația definitivă

După închiderea anuală există etapa de situație definitivă, disponibilă numai în condițiile prevăzute de sistem. Ea verifică existența și coerența închiderii înainte de înregistrare.

Cu alte cuvinte, nu punem acoperișul înainte să vedem dacă avem pereți. 😄

---

# 🔄 PARTEA III — CUM CIRCULĂ INFORMAȚIA ÎNTRE CELE DOUĂ APLICAȚII

## 23. Părinte → diriginte

Din Portalul Părinților pot porni:
- documente pentru dosarul elevului;
- scutiri medicale;
- documente pentru bursă;
- cereri de motivare a absențelor;
- solicitări de învoire.

Acestea sunt înregistrate în fluxurile lor și devin vizibile dirigintelui în zonele corespunzătoare/Inbox.

## 24. Diriginte → părinte

Din aplicația profesorului pot porni:
- înștiințări și documente ale școlii;
- actualizări/comunicări privind situația școlară;
- răspunsul operațional la solicitarea de învoire, inclusiv aprobarea și biletul atunci când este cazul.

Părintele le vede în portal, iar pentru documentele școlii sistemul poate păstra confirmarea primei accesări.

## 25. Catalog → ambele părți

Catalogul este sursa situației școlare. Profesorul lucrează în aplicația lui cu operațiile autorizate; părintele vede situația elevului în portal. Neluțu explică, dar nu devine a treia mână care scrie în catalog.

---

# 🛡️ PARTEA IV — REGULA DE AUR

Tot sistemul este construit în jurul unei idei simple:

**Zero pierderi de date. Zero pierderi de funcționalități existente. Nicio schimbare de comportament fără autorizare și verificare.**

De aceea există validări de structură și identitate, verificări înainte de scriere, protecții anti-duplicare unde fluxul o cere, backupuri pentru operațiile sensibile, registre separate pentru stări importante și blocarea operației când sistemul nu poate demonstra că este sigură.

Iar eu, Neluțu, respect aceeași regulă. Pot să te îndrum, să-ți explic, să-ți spun unde-i butonul și de ce nu-i bine să apeși aiurea. Pot să mai și glumesc, că doar n-om face școala cu fața ca la controlul fiscal. 😄 Dar nu inventez date, nu mă dau director, nu mă substitui profesorului și nu schimb evidențe pe ascuns.

---

# 🤠 PARTEA V — CUM MĂ FOLOSEȘTI PE MINE

**Dacă apeși pe brâul meu**, ajungi la tutorialul ăsta — povestea mare a sistemului.

**Dacă apeși direct pe mine**, se deschide fereastra simplă de întrebări și răspunsuri. Poți întreba firesc: „unde bag scutirea?”, „cum văd ce-o trimis școala?”, „ce înseamnă învoire în așteptare?”, „unde văd absențele?”, „ce face dirigintele cu documentul?” sau alte întrebări despre sistem.

Nu trebuie să vorbești ca un manual. Spune cum știi. Io încerc să pricep. Dacă întrebarea-i serioasă, răspund serios. Dacă-i loc de-o glumă, no... doar n-oi lăsa Ardealul de rușine. 😄

Și mai am un obicei: **mă uit atent la cum lucrii**. Dacă sistemul îmi permite să observ că te-ai încurcat într-un flux și am o intervenție sigură, pot să-ți dau un ghiont prietenos. Nu te bat la cap și nu iau decizii în locul tău.

No, amu știi tătă povestea. Dacă ai citit până aici, meriți ori o cafea, ori zece la purtare. Cafeaua pot s-o recomand; nota, vezi bine, nu-i treaba mea. 🤠😄"""

def _norm(text):
    text=unicodedata.normalize("NFKD",str(text or ""))
    text="".join(ch for ch in text if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+"," ",text).strip()

# Prioritate pentru intențiile concrete; fără potriviri pe fragmente de cuvinte.
# Folosim doar biblioteca standard, fără AI/API extern.
ALIASES={
"tutorial":("tutorial","ghid complet","prezinta sistemul","arata mi aplicatia","explica mi aplicatia","cum folosesc tot","cum merge tot"),
"medical":("unde bag scutirea","scutire medicala","adeverinta medicala","trimit scutirea","unde trimit adeverinta","incarc scutirea","depun scutirea","scutirea copilului"),
"excuse":("motivez absente","motivare absente","motivarea absentelor","cerere de motivare","mai trebe sa duc","mai trebuie sa duc","cererea pe hartie","cererea tiparita","cum justific absentele"),
"leave":("invoire","invoirea","iau copilul","plece de la scoala","cer voie","bilet de voie","pleaca mai devreme","sa plece acasa"),
"sent":("ce am trimis","s a trimis","document transmis","cum stiu ca am trimis","unde vad actele trimise","a ajuns documentul","am depus cererea"),
"school":("unde vad ce o trimis scoala","ce a trimis scoala","instiintare","mesaj de la scoala","notificare de la scoala","confirmare de primire","unde vad comunicarile"),
"documents":("trimit hartia","trimit actul","trimit la dirigu","incarc document","unde incarc","dosar personal","dosar bursa","unde pun documentele"),
}
def _contains_phrase(text, phrase):
    # Delimitare de cuvinte: «pin» nu trebuie găsit în «opinii».
    return bool(re.search(r"(?<![a-z0-9])"+re.escape(_norm(phrase))+r"(?![a-z0-9])", text))

def _match(q):
    nq=_norm(q)
    if not nq: return None
    # Expresiile specifice câștigă în fața celor generale.
    hits=[]
    for priority,(intent,phrases) in enumerate(ALIASES.items()):
        for phrase in phrases:
            normalized=_norm(phrase)
            if _contains_phrase(nq,normalized):
                hits.append((len(normalized.split()),len(normalized),-priority,intent))
    return max(hits)[3] if hits else None

def answer_parent(question,context=None):
    # Nu lăsăm aliasurile să mascheze situațiile de siguranță.
    safety=_base_answer(question,context)
    if safety.intent=="safety":
        return safety
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
