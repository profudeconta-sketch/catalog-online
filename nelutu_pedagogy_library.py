"""Bibliotecă pedagogică locală: orientare generală, fără diagnostic sau informații pretins actualizate."""
from __future__ import annotations
import re
import unicodedata
from nelutu_assistant import NelutuAnswer

def norm(text):
    text=unicodedata.normalize("NFKD",str(text or ""))
    text="".join(c for c in text if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+"," ",text).strip()

LIBRARY={
 "cuza":(("alexandru ioan cuza","reforma din 1864","legea instructiunii publice"),"În timpul domniei lui Alexandru Ioan Cuza, Legea instrucțiunii publice din 1864 a reprezentat un reper pentru organizarea învățământului modern și pentru principiul obligativității instrucțiunii primare. Istoria aplicării ei în practică a fost însă mai complicată decât textul legii.","Vă interesează reforma propriu-zisă sau cum arăta viața elevilor atunci?"),
 "haret":(("spiru haret","haret"),"Spiru Haret a fost o figură importantă a modernizării școlii românești, susținând organizarea educației, pregătirea cadrelor didactice și rolul școlii în comunitate. E util să deosebim reformele propuse de rezultatele lor, care au variat în timp și între regiuni.","Vreți să discutăm despre reformele sale sau despre ce putem învăța astăzi din ele?"),
 "interwar":(("interbelic","perioada interbelica","intre razboaie"),"În perioada interbelică, sistemul românesc de învățământ a trecut prin eforturi de unificare și extindere, pe fondul diferențelor regionale și sociale. Accesul la școală și condițiile de studiu nu erau egale pentru toți copiii.","Vă interesează școala rurală, liceele ori învățământul profesional din acea perioadă?"),
 "communism":(("comunism","comunist","inainte de 1989"),"În perioada comunistă, școala a cunoscut extinderea accesului la educație și o legătură puternică între pregătirea tehnică și economia planificată. În același timp, controlul ideologic și restricțiile asupra libertății de exprimare au afectat educația.","Vreți să comparăm pregătirea practică de atunci cu cea de astăzi, fără să idealizăm niciuna dintre perioade?"),
 "post1989":(("revolutia din 1989","dupa 1989","postcomunist","tranzitia scolii"),"După 1989, învățământul românesc a trecut prin schimbări de programe, instituții, evaluare și orientare către standarde europene. Reformele au fost succesive, iar efectele lor nu au fost uniforme. Pentru prevederile valabile astăzi trebuie consultate actele oficiale actualizate.","Vă interesează schimbările de curriculum, examenele sau învățământul tehnologic?"),
 "pedagogy":(("pedagogie moderna","pedagogia moderna","pedagogia in trecut","metode de predare","invatare activa","predare moderna"),"No, odinioară predarea punea adesea accent mai mare pe memorare, disciplină și expunerea profesorului. Pedagogia contemporană valorifică și participarea activă, feedbackul, diferențierea și înțelegerea, fără să renunțe la exercițiu, cunoștințe ori reguli. Nu orice metodă veche era greșită și nici orice metodă nouă nu-i automat bună.","Doriți un exemplu concret: aceeași lecție predată tradițional și apoi printr-o activitate practică?"),
 "adolescent":(("adolescent","adolescenta","pubertate","copilul nu ma asculta","se cearta cu mine","nu comunica cu mine","sta numai pe telefon","dependenta de telefon","antura","presiunea grupului"),"No, adolescența aduce nevoia de autonomie, sensibilitate la relațiile cu ceilalți și schimbări în felul în care tinerii gestionează emoțiile. Ajută să ascultăm înainte să judecăm, să stabilim limite clare împreună și să discutăm despre consecințe fără umilire. Nu pot stabili un diagnostic sau explica sigur comportamentul unui copil doar din câteva cuvinte.","Ce vârstă are copilul și ce situație concretă vă îngrijorează? Nu e nevoie să-mi spuneți numele ori date personale."),
 "technical":(("invatamant tehnologic","invatamant profesional","meserie","meserii","practica in atelier","educatie tehnica"),"No, o meserie învățată temeinic nu exclude facultatea, după cum studiile universitare nu înlocuiesc automat priceperea practică. Învățământul tehnic poate uni teoria cu aplicarea ei, dezvoltând responsabilitate, gândire practică și competențe transferabile. Alegerea trebuie să țină cont de aptitudinile și dorințele elevului, nu de prejudecăți.","Ce îi place copilului să facă practic și ce drum ar vrea să urmeze după liceu?")
}

def lookup(question):
    q=norm(question)
    hits=[]
    for key,(terms,answer,followup) in LIBRARY.items():
        for term in terms:
            t=norm(term)
            if re.search(r"(?<![a-z0-9])"+re.escape(t)+r"(?![a-z0-9])",q):
                hits.append((len(t.split()),len(t),key))
    if not hits:
        return None
    key=max(hits)[2]
    _,answer,followup=LIBRARY[key]
    return NelutuAnswer("library_"+key,"No, hai să desfacem subiectul pe îndelete. 🤠 "+answer+"\n\n"+followup)

def clarify(question):
    q=norm(question)
    if not q:
        return None
    if any(w in q.split() for w in ("cum","unde","cand","de","ce","pot","vreau","ajutor","problema")):
        return NelutuAnswer("clarification","No, vreau să-ți răspund la obiect, nu din clop. 🤠 Te referi la **o operație din portal**, la **școala și educația copilului** sau la **istoria și regulile învățământului**? Spune-mi și ce anume vrei să afli, iar io încerc să lămuresc pas cu pas.")
    return None

def contract():
    return {"writes_data":False,"network":False,"paid_ai":False,"diagnoses":False,"claims_live_updates":False}
