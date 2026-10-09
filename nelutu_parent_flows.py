"""Ghid unificat, determinist, pentru toate fluxurile Portalului Părinților.

Nu accesează date personale, nu trimite documente și nu execută operații.
"""
from nelutu_assistant import NelutuAnswer
from nelutu_local_dialogue import _norm

SENT = ("După confirmarea transmiterii, verifică în **📁 Documente → "
        "Documente deja transmise dirigintelui**; acolo poți selecta "
        "documentul înregistrat și îl poți descărca.")
UPLOAD = ("Selectează **Tipul documentului**, încarcă un fișier PDF, JPG/JPEG "
          "sau PNG și apasă **📤 Salvează și trimite**. Simpla selectare sau "
          "încărcare a fișierului **nu înseamnă transmitere**. Așteaptă "
          "mesajul «Documentul a fost salvat și înregistrat. "
          "Transmiterea a fost confirmată». ")
PREFIX = "No, după autentificare în Portalul Părinților, "
END = " Eu te îndrum, dar nu transmit și nu aprob nimic în locul tău. 🤠"

PERSONAL = {
    "carte de identitate": ("carte", "identitate", "buletin"),
    "dovadă adresă": ("adresa", "domiciliu"),
    "certificat de naștere": ("nastere", "certificat"),
    "alte documente (Diverse)": ("diverse",),
}
BURSA = {
    "Merit": ("merit",),
    "Socială – venit": ("venit", "venituri"),
    "Socială – orfan": ("orfan", "orfana"),
    "Socială – medicală": ("medicala", "medical"),
    "Mame minore": ("mame minore", "mama minora"),
    "CES": ("ces",),
}
BURSA_DOCUMENTE = (
    "cerere bursă, acord de prelucrare a datelor, declarație de venituri nete "
    "impozabile, documente medicale, CI părinte/tutore, certificate de naștere "
    "frați/surori, certificat de căsătorie, hotărâre/sentință de divorț, "
    "certificat de deces părinte și alte documente justificative"
)

def _has(q, *terms):
    return any(term in q for term in terms)

def answer(question):
    q = _norm(question)
    if not q:
        return None
    words = set(q.split())
    # Nu interceptăm întrebări educaționale sau administrative fără legătură.
    portal = _has(q, "document", "act", "incarc", "trimit", "transmit",
                  "depun", "dosar", "scutir", "bursa", "motiv", "invoir",
                  "instiint", "scoala", "confirm", "primit", "verific",
                  "dovada adresa", "identitate", "buletin", "nastere")
    if not portal:
        return None

    # Întrebările de ansamblu au prioritate față de orice subiect individual.
    comprehensive = _has(q, "toate sectiunile", "intregul portal", "tot portalul",
                         "ghid complet", "tutorial complet", "cap coada",
                         "nu omite nicio sectiune", "toate functionalitatile")
    multi_section = sum((
        _has(q, "invoir", "bilet de voie"),
        _has(q, "scutir", "medical"),
        _has(q, "bursa", "burse"),
        _has(q, "dosar personal", "acte"),
        _has(q, "motivare", "absent"),
        _has(q, "instiint", "scoala"),
    )) >= 3 and _has(q, "explica", "prezinta", "pas cu pas", "vreau sa inteleg")
    if comprehensive or multi_section:
        msg = (PREFIX +
               "**Portalul are trei secțiuni principale: 🔔 Școală, 🚪 Învoire și 📁 Documente.**\n\n"
               "**1. 🔔 Școală:** alegi înștiințarea și apeși "
               "**«📄 Deschide documentul și confirmă luarea la cunoștință»**. "
               "Prima accesare se înregistrează cu data și ora și este vizibilă dirigintelui. "
               "Notificarea WhatsApp nu înlocuiește confirmarea din portal.\n\n"
               "**2. 🚪 Învoire:** soliciți plecarea numai pentru ziua curentă, "
               "cu motiv și oră viitoare. Trimiți cererea și urmărești starea: "
               "**În așteptare** nu înseamnă **Aprobată**. După aprobare apare "
               "biletul de voie; dacă ora trece fără aprobare, solicitarea "
               "poate expira și este considerată refuzată. Biletul nu motivează absențele.\n\n"
               "**3. 📁 Documente → 👤 Dosar personal:** alegi tipul "
               "(carte de identitate, dovadă adresă, certificat de naștere sau Diverse), "
               "selectezi PDF/JPG/JPEG/PNG și apeși **📤 Salvează și trimite**.\n\n"
               "**4. 📁 Documente → 🏥 Scutiri medicale:** alegi tipul, "
               "încarci documentul și apeși **📤 Salvează și trimite**.\n\n"
               "**5. 📁 Documente → 🎓 Dosar bursă:** alegi una dintre cele șase "
               "secțiuni: **Merit, Socială – venit, Socială – orfan, "
               "Socială – medicală, Mame minore, CES**. Alegi tipul actului "
               "(de exemplu: " + BURSA_DOCUMENTE + "), încarci fișierul și "
               "apeși **📤 Salvează și trimite**. Depunerea actelor nu "
               "înseamnă aprobarea bursei.\n\n"
               "**6. 📁 Documente → 📝 Motivare absențe părinte:** alegi "
               "părintele, data și numărul de ore, verifici plafonul disponibil. "
               "Previzualizarea PDF nu transmite cererea. Numai **📨 Generează, "
               "salvează și trimite**, urmat de confirmarea portalului, "
               "înregistrează cererea ca depusă.\n\n"
               "**7. Verificarea transmiterii:** la documentele încărcate, "
               "simpla alegere a fișierului **nu înseamnă transmitere**. "
               "Aștepți mesajul «Documentul a fost salvat și înregistrat. "
               "Transmiterea a fost confirmată». Apoi intri la **📁 Documente "
               "→ Documente deja transmise dirigintelui**, selectezi "
               "documentul și îl poți descărca. Învoirea se verifică separat "
               "după starea solicitării; înștiințările după confirmarea accesării.")
        return NelutuAnswer("parent_flow_complete", msg + END)

    if _has(q, "invoir", "bilet de voie", "plece mai devreme", "pleaca mai devreme"):
        msg = (PREFIX + "deschizi **🚪 Învoire**, completezi solicitarea "
               "pentru **ziua curentă**, alegi motivul și o oră viitoare, "
               "apoi trimiți cererea. Verifică mesajul de transmitere și "
               "starea solicitării: **În așteptare** nu înseamnă **Aprobată**. "
               "Numai după aprobarea dirigintelui apare biletul de voie; "
               "dacă ora trece fără aprobare, solicitarea poate expira și "
               "este considerată refuzată. Biletul nu motivează automat absențe.")
        return NelutuAnswer("parent_flow_leave", msg + END)

    if _has(q, "motivare", "motivez", "motiv", "absent") and not _has(q, "medicala", "scutire medicala"):
        msg = (PREFIX + "deschizi **📁 Documente → 📝 Motivare absențe părinte**. "
               "Alegi părintele, data absenței și numărul de ore; verifici "
               "orele disponibile afișate de portal. Poți genera o "
               "**previzualizare PDF**, dar aceasta **nu transmite cererea** "
               "și nu consumă ore. Apasă **📨 Generează, salvează și trimite** "
               "și așteaptă confirmarea că cererea a fost transmisă și "
               "considerată depusă. După confirmare nu trebuie adusă "
               "aceeași cerere tipărită; dacă apar probleme, dirigintele "
               "te contactează separat.")
        return NelutuAnswer("parent_flow_excuse", msg + END)

    if _has(q, "instiint", "de la scoala", "scoala mi", "scoala a", "confirmare de primire", "luarea la cunostinta"):
        msg = (PREFIX + "mergi la **🔔 Școală** și alegi înștiințarea. "
               "Apasă **📄 Deschide documentul și confirmă luarea la cunoștință**. "
               "Abia această acțiune înregistrează prima accesare, cu data "
               "și ora, vizibilă dirigintelui. Poți descărca documentul "
               "după deschidere; o alertă WhatsApp nu înlocuiește confirmarea din portal.")
        return NelutuAnswer("parent_flow_school", msg + END)

    if _has(q, "bursa", "bursei", "burse", "merit", "orfan", "mame minore", "ces", "venituri nete"):
        subtype = next((name for name, aliases in BURSA.items()
                        if any(a in q for a in aliases)), None)
        route = "**📁 Documente → 🎓 Dosar bursă**"
        if subtype:
            route += " → **" + subtype + "**"
        msg = (PREFIX + "mergi la " + route + ". Selectezi tipul de bursă "
               "potrivit și tipul documentului. Categoriile disponibile "
               "includ: " + BURSA_DOCUMENTE + ". " + UPLOAD + SENT +
               " Transmiterea documentelor nu înseamnă aprobarea bursei.")
        return NelutuAnswer("parent_flow_scholarship", msg + END)

    if _has(q, "scutir", "adeverinta medicala", "certificat medical"):
        msg = (PREFIX + "mergi la **📁 Documente → 🏥 Scutiri medicale**. "
               + UPLOAD + SENT)
        return NelutuAnswer("parent_flow_medical", msg + END)

    if _has(q, "dosar personal", "identitate", "buletin", "dovada adresa",
            "certificat de nastere", "document personal", "acte personale"):
        msg = (PREFIX + "mergi la **📁 Documente → 👤 Dosar personal**. "
               "Poți selecta carte de identitate, dovadă adresă, certificat "
               "de naștere sau Diverse, conform tipurilor din formular. "
               + UPLOAD + SENT)
        return NelutuAnswer("parent_flow_personal", msg + END)

    if _has(q, "ce am trimis", "deja transmise", "verific document",
            "a ajuns document", "document transmis", "documentele trimise"):
        return NelutuAnswer("parent_flow_sent", PREFIX + SENT + END)

    if _has(q, "document", "incarc", "trimit act", "trimit hartia", "unde pun"):
        msg = (PREFIX + "deschizi **📁 Documente** și alegi "
               "**👤 Dosar personal**, **🏥 Scutiri medicale**, "
               "**🎓 Dosar bursă** sau **📝 Motivare absențe părinte**, "
               "după situație. Pentru documentele încărcate, " + UPLOAD +
               SENT + " Pentru motivare, folosești butonul distinct "
               "**📨 Generează, salvează și trimite**.")
        return NelutuAnswer("parent_flow_documents", msg + END)
    return None
