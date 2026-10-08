"""Dialog educațional local, determinist și fără acces la date, rețea ori API."""
from __future__ import annotations
import hashlib
import re
import unicodedata
from nelutu_assistant import NelutuAnswer

def _norm(value):
    value=unicodedata.normalize("NFKD",str(value or ""))
    value="".join(ch for ch in value if not unicodedata.combining(ch)).lower()
    return re.sub(r"[^a-z0-9]+"," ",value).strip()

# Fiecare subiect are o explicație și o întrebare deschisă, fără judecăți despre elev.
TOPICS={
 "technical": {
  "terms":("invatamant tehnic","invatamantul tehnic","liceu tehnologic","scoala profesionala","meserie","meserii","practica","atelier","calificare","tehnician","munca manuala"),
  "thoughts":(
   "No, o meserie bine învățată îi o formă de pricepere și de demnitate. În învățământul tehnic, teoria capătă rost când elevul vede ce poate construi, repara ori îmbunătăți.",
   "Apăi, cartea și meseria nu-s dușmani. Matematica, comunicarea și tehnologia pot merge mână-n mână cu practica din atelier.",
   "No, învățământul tehnic nu trebuie privit ca o alegere de mâna a doua. Poate deschide drumuri spre angajare, specializare ori studii mai departe; important îi să se potrivească intereselor copilului."
  ),
  "questions":("Ce credeți că l-ar atrage mai mult pe copil: să înțeleagă cum funcționează ceva sau să construiască el însuși?","Ce meserie sau activitate practică i-a stârnit curiozitatea până acum?")
 },
 "purpose":{
  "terms":("rostul scolii","de ce invatam","de ce scoala","importanta educatiei","educatia","rostul educatiei","importanta invatamantului","educatie","invatatura","invatamant","scoala in viata"),
  "thoughts":(
   "No, școala nu-i numai despre note. Îl ajută pe om să gândească, să pună întrebări, să înțeleagă lumea și să aleagă cu mintea lui.",
   "Apăi, educația nu promite că viața va fi ușoară, da' îi dă omului mai multe unelte să se descurce cu ea.",
   "No, o lecție bună nu-i doar aceea pe care o ții minte până la test, ci și aceea care te ajută să judeci singur o situație."
  ),
  "questions":("Dumneavoastră ce credeți că ar trebui să rămână cu un copil după ce uită formulele din manual?","Care a fost lecția de la școală care v-a folosit cel mai mult în viață?")
 },
 "motivation":{
  "terms":("nu vrea sa invete","nu ii place scoala","nu i place scoala","motivatia","motivatie","fara chef","renunta la scoala","nu are rost sa invete","dezinteres"),
  "thoughts":(
   "No, când copilul nu mai vede rostul școlii, o ceartă în plus rareori îi aprinde curiozitatea. Mai folositor poate fi să aflăm ce-l apasă și ce i-ar da un scop concret.",
   "Apăi, motivația nu vine totdeauna înaintea muncii. Uneori începe cu o reușită mică, pe care copilul o poate vedea și de care poate fi mândru.",
   "No, fiecare elev are ritmul lui. Îi bine să cerem efort, da' și să-l ajutăm să observe progresul, nu doar greșeala."
  ),
  "questions":("Ați observat vreo activitate la care copilul prinde curaj și nu se lasă ușor?","Ce anume pare să-l descurajeze cel mai mult: dificultatea, lipsa interesului sau teama de eșec?")
 },
 "family":{
  "terms":("parintii si scoala","parinte si profesor","familia si scoala","rolul parintilor","sprijinul familiei","comunicarea cu profesorii","colaborarea cu scoala"),
  "thoughts":(
   "No, școala și familia nu trag două căruțe diferite. Când își vorbesc cu respect, copilul primește un mesaj mai limpede despre responsabilitate.",
   "Apăi, un părinte nu trebuie să știe toate lecțiile ca să sprijine învățarea. Uneori contează mai mult să asculte, să întrebe și să fie prezent.",
   "No, profesorul vede copilul într-un fel, familia în altul. Împreună pot înțelege mai bine ce ajutor îi trebuie."
  ),
  "questions":("Ce fel de comunicare cu școala vi s-ar părea cea mai folositoare?","Unde credeți că ar ajuta cel mai mult o colaborare mai apropiată între familie și profesori?")
 },
 "future":{
  "terms":("viitorul copilului","viitorul elevului","cariera","alegerea profesiei","alegerea meseriei","ce va face in viitor","dupa liceu"),
  "thoughts":(
   "No, viitorul nu-i o potecă trasată dinainte. Școala poate să-i dea copilului opțiuni, iar alegerea bună se construiește cunoscându-și interesele și posibilitățile.",
   "Apăi, o meserie învățată temeinic poate fi un început, nu o limită. Oamenii continuă să învețe și după ce termină liceul.",
   "No, mai sănătos decât să ghicim profesia perfectă îi să descoperim ce știe copilul să facă, ce-i place și ce poate exersa."
  ),
  "questions":("Ce activități îi plac copilului suficient de mult încât să le facă și fără să-l îndemne cineva?","Vă gândiți mai mult la continuarea studiilor, la o meserie sau încă explorați posibilitățile?")
 }
}

def educational_reply(question):
    q=_norm(question)
    if not q:
        return None
    candidates=[]
    for key,topic in TOPICS.items():
        matches=[term for term in topic["terms"] if re.search(r"(?<![a-z0-9])"+re.escape(_norm(term))+r"(?![a-z0-9])",q)]
        if matches:
            candidates.append((max(len(_norm(t).split()) for t in matches),max(len(_norm(t)) for t in matches),key))
    if not candidates:
        return None
    key=max(candidates)[2]
    topic=TOPICS[key]
    digest=hashlib.sha256(q.encode("utf-8")).digest()
    thought=topic["thoughts"][digest[0]%len(topic["thoughts"])]
    followup=topic["questions"][digest[1]%len(topic["questions"])]
    return NelutuAnswer("education_"+key,thought+"\n\n"+followup)

def contract():
    return {"writes_data":False,"uses_network":False,"external_ai":False,"reads_student_records":False}
