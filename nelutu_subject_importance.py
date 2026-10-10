"""Explicații despre utilitatea disciplinelor IX TH; fără acces la date personale."""
from __future__ import annotations
import re
import unicodedata
from nelutu_assistant import NelutuAnswer

def _norm(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()

SUBJECTS = [["romana",["limba si literatura romana","limba romana","romana"],"Limba și literatura română","te ajută să înțelegi texte, să-ți exprimi ideile limpede și să verifici informațiile","scrii un mesaj corect unui client sau înțelegi un contract"],["engleza",["limba engleza","engleza","english"],"Limba engleză","îți permite să comunici cu oameni din alte țări și să folosești resurse internaționale","primești un turist străin și îi explici serviciile hotelului"],["franceza",["limba franceza","franceza"],"Limba franceză","îți dezvoltă comunicarea într-o altă limbă și înțelegerea altor culturi","îndrumi un oaspete francofon sau citești o ofertă turistică"],["matematica",["matematica"],"Matematica","îți formează gândirea logică și te ajută să calculezi corect","calculezi reduceri, restul, bugete sau gradul de ocupare"],["fizica",["fizica"],"Fizica","explică forțele, energia, mișcarea și funcționarea aparatelor","înțelegi de ce un aparat electric consumă energie și cum îl folosești în siguranță"],["chimia",["chimie","chimia"],"Chimia","te ajută să înțelegi substanțele și transformările lor","citești corect eticheta unui produs de curățenie și eviți amestecurile periculoase"],["biologia",["biologie","biologia"],"Biologia","te ajută să înțelegi corpul, sănătatea și mediul viu","înțelegi igiena alimentară și de ce prevenirea contaminării contează"],["istoria",["istorie","istoria"],"Istoria","te învață să înțelegi cauze, consecințe și să compari sursele","prezinți unui turist povestea unui monument fără să inventezi fapte"],["geografia",["geografie","geografia"],"Geografia","te ajută să înțelegi locurile, clima, resursele și orientarea","recomanzi trasee turistice potrivite regiunii și sezonului"],["logica",["logica argumentare si comunicare","logica","argumentare si comunicare"],"Logica, argumentarea și comunicarea","te ajută să recunoști argumentele bune și să explici coerent o decizie","rezolvi politicos o reclamație, separând faptele de presupuneri"],["tic",["informatica tic","informatica","tic","tehnologia informatiei"],"Informatica / TIC","te învață să folosești responsabil instrumente digitale și să organizezi informații","lucrezi cu tabele, rezervări și documente electronice"],["sport",["educatie fizica","sport"],"Educația fizică","susține sănătatea, coordonarea, cooperarea și disciplina","îți formezi obiceiuri de mișcare utile și la un loc de muncă solicitant"],["religia",["religie","religia"],"Religia","poate contribui la reflecția asupra valorilor, tradițiilor și respectului pentru ceilalți","înțelegi mai bine obiceiurile și patrimoniul cultural al comunităților"],["arte",["arte vizuale si educatie plastica","arte vizuale","educatie plastica"],"Artele vizuale și educația plastică","îți dezvoltă observația, creativitatea și sensibilitatea estetică","realizezi o prezentare vizuală clară pentru un serviciu turistic"],["m1",["m1","bazele contabilitatii","bazele contabilitatii"],"M1 – Bazele contabilității","te învață să urmărești documente, bunuri, datorii, venituri și cheltuieli","verifici o factură și înțelegi cum se evidențiază o încasare"],["m2",["m2","etica si comunicare","etica"],"M2 – Etică și comunicare","formează comunicarea profesională, respectul și luarea deciziilor responsabile","tratezi corect un client și protejezi informațiile confidențiale"],["m3",["m3","structuri de primire turistica","structuri de primire"],"M3 – Structuri de primire turistică","explică tipurile de unități de cazare și serviciile oferite oaspeților","deosebești un hotel de o pensiune și înțelegi etapele primirii unui turist"],["m4",["m4","procese si calitate in horeca","procese si calitate","horeca"],"M4 – Procese și calitate în HoReCa","te ajută să înțelegi organizarea serviciilor, igiena și controlul calității","verifici pașii unui serviciu astfel încât clientul să fie servit corect și în siguranță"],["m5",["m5","cdeos ip","instruire practica"],"M5 – CDEOȘ (IP) – Instruire practică","îți oferă ocazia să exersezi competențe în situații apropiate de muncă","aplici concret reguli de lucru, comunicare și siguranță"],["m6",["m6","curriculum de aprofundare si insertie profesionala","insertie profesionala","curriculum de aprofundare"],"M6 – Curriculum de aprofundare și inserție profesională","consolidează competențele și pregătește trecerea către activități profesionale","exersezi prezentarea propriilor abilități și rezolvarea unei sarcini de serviciu"]]

PURPOSE = ("de ce", "la ce", "folos", "importan", "rost", "trebuie", "trebe", "invatam", "invat", "facem", "fac", "ajuta", "util", "meserie", "viata", "explica", "spune mi", "ce este", "ce inseamna")

def subject_reply(question):
    q = _norm(question)
    if not q:
        return None
    matches = []
    for key, aliases, title, importance, example in SUBJECTS:
        for alias in aliases:
            a = _norm(alias)
            if re.search(r"(?<![a-z0-9])" + re.escape(a) + r"(?![a-z0-9])", q):
                matches.append((len(a), key, title, importance, example))
    if not matches:
        return None
    _, key, title, importance, example = max(matches, key=lambda item: item[0])
    if not any(marker in q for marker in PURPOSE) and q not in (_norm(title), key):
        return None
    return NelutuAnswer("subject_" + key, "No, " + title + " are un rost cât se poate de practic: " + importance + ". De pildă, " + example + ". 🤠 Nu-i numai pentru o notă; îi o pricepere care poate prinde bine în viață!")
