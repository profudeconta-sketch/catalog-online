"""Neluțu Cloudflare Workers AI: prototip opt-in, fără acces la date școlare.

Nu este activ implicit. Nu transmite conversații, identități sau documente
decât după configurarea explicită și integrarea aprobată în portal.
"""
from __future__ import annotations
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

DEFAULT_MODEL="@cf/qwen/qwen3-30b-a3b-fp8"
MAX_QUESTION=1200
MAX_HISTORY=4
MAX_RESPONSE=2200

SYSTEM_PROMPT=(
    "Ești Neluțu, asistentul educațional al Portalului Părinților, cu "
    "grai cald ardelenesc de pe Valea Arieșului. Vorbești în română clară, "
    "natural, cu umor discret; nu repeta mecanic aceeași formulă. "
    "Discuți despre educație, pedagogie, adolescență, meserii și istoria școlii. "
    "Nu inventa legi actuale, date istorice, situații școlare ori funcții de portal. "
    "Dacă nu știi sau întrebarea este ambiguă, cere o lămurire precisă. "
    "Nu diagnostica persoane și nu recomanda sancțiuni sau tratamente. "
    "Nu solicita nume, CNP, PIN, note, documente sau alte date personale. "
    "Nu pretinde că poți modifica datele școlii sau trimite documente. "
    "Explică valoarea învățământului tehnic fără a disprețui educația teoretică. "
    "La risc imediat, recomandă sprijin uman urgent. "
    "Răspunde concis, cu exemple concrete când ajută."
)

@dataclass(frozen=True)
class AIResult:
    text: str
    available: bool
    reason: str = ""

class AIUnavailable(Exception):
    pass

# Politică strictă: numai teme educaționale generale. Întrebările despre
# elevul concret sau despre operații din portal rămân la motorul local.
PRIVATE_PATTERNS=(
    r"\b(?:pin|parola|cnp|matricol|catalog|nota|note|medie|absent[ae]|scutire|motivare|"
    r"invoire|document|dosar|bursa|burse|instiintare|whatsapp|telefon|adresa|"
    r"elevul meu|fiul meu|fiica mea|copilul meu|al meu|a mea)\b",
    r"\b[0-9]{9,}\b",
    r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b",
)
GENERAL_TOPICS=(
    "educatie","invatamant","pedagog","adolescent","meserie","profesional",
    "tehnic","scoala","profesor","parinte","familie","invatare","motivatie",
    "istorie","cuza","haret","interbelic","comunism","facultate","cariera",
    "copii","copil","tineri","revolutia","1989",
)

def _ascii(value):
    import unicodedata
    value=unicodedata.normalize("NFKD",str(value or ""))
    return "".join(c for c in value if not unicodedata.combining(c)).lower()

def eligible(question):
    q=_ascii(question).strip()
    if not q or len(q)>MAX_QUESTION:
        return False
    if any(re.search(pattern,q,re.I) for pattern in PRIVATE_PATTERNS):
        return False
    return any(re.search(r"(?<![a-z])"+re.escape(topic)+r"[a-z]*(?![a-z])",q) for topic in GENERAL_TOPICS)

def _messages(question,history):
    messages=[{"role":"system","content":SYSTEM_PROMPT}]
    for item in (history or [])[-MAX_HISTORY:]:
        if not isinstance(item,dict):
            continue
        role=item.get("role")
        content=item.get("content")
        if role in ("user","assistant") and isinstance(content,str) and len(content)<=MAX_QUESTION and (role!="user" or eligible(content)):
            messages.append({"role":role,"content":content})
    messages.append({"role":"user","content":question})
    return messages

def generate(question,*,account_id="",api_token="",model=DEFAULT_MODEL,history=None,transport=None):
    """Returnează AIUnavailable fără rețea dacă nu există configurare sau eligibilitate."""
    if not eligible(question):
        raise AIUnavailable("not_eligible")
    if not account_id or not api_token:
        raise AIUnavailable("not_configured")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,64}",account_id):
        raise AIUnavailable("invalid_account")
    if not model.startswith("@cf/"):
        raise AIUnavailable("invalid_model")
    url="https://api.cloudflare.com/client/v4/accounts/"+account_id+"/ai/run/"+model
    payload=json.dumps({"messages":_messages(question,history),"max_tokens":400}).encode("utf-8")
    request=urllib.request.Request(url,data=payload,headers={
        "Authorization":"Bearer "+api_token,
        "Content-Type":"application/json",
    },method="POST")
    opener=transport or urllib.request.urlopen
    try:
        with opener(request,timeout=18) as response:
            body=response.read(131072)
        data=json.loads(body)
        result=data.get("result") or {}
        answer=result.get("response")
        if not data.get("success",False) or not isinstance(answer,str) or not answer.strip():
            raise AIUnavailable("invalid_response")
        return AIResult(answer.strip()[:MAX_RESPONSE],True)
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,KeyError) as exc:
        raise AIUnavailable("provider_unavailable") from exc

def contract():
    return {"opt_in":True,"writes_student_data":False,"uses_paid_api":False,
            "external_processing_when_enabled":True,"forwards_student_records":False}
