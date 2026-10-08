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
from nelutu_ai_experiment import NELUTU_PERSONA, ExperimentalPolicy
from nelutu_ai_privacy import approved_external_question, external_messages

DEFAULT_MODEL="@cf/qwen/qwen3-30b-a3b-fp8"
MAX_QUESTION=1200
MAX_HISTORY=4
MAX_RESPONSE=2200

SYSTEM_PROMPT = NELUTU_PERSONA

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
    "educatie","invatamant","matematic","pedagog","adolescent","meserie","profesional",
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
    if not approved_external_question(question):
        raise AIUnavailable("not_eligible")
    if not account_id or not api_token:
        raise AIUnavailable("not_configured")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,64}",account_id):
        raise AIUnavailable("invalid_account")
    if not model.startswith("@cf/"):
        raise AIUnavailable("invalid_model")
    url="https://api.cloudflare.com/client/v4/accounts/"+account_id+"/ai/run/"+model
    payload=json.dumps({"messages":external_messages(question,SYSTEM_PROMPT),"max_tokens":ExperimentalPolicy().max_output_tokens}).encode("utf-8")
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
        choices=result.get("choices") or []
        if choices and isinstance(choices[0],dict) and choices[0].get("finish_reason") == "length":
            raise AIUnavailable("truncated_response")
        if not data.get("success",False) or not isinstance(answer,str) or not answer.strip():
            raise AIUnavailable("invalid_response")
        return AIResult(answer.strip()[:MAX_RESPONSE],True)
    except AIUnavailable:
        raise
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,KeyError) as exc:
        raise AIUnavailable("provider_unavailable") from exc

def contract():
    return {"opt_in":True,"writes_student_data":False,"free_tier_only_not_guaranteed":True,"billing_must_be_disabled_or_capped":True,
            "external_processing_when_enabled":True,"forwards_student_records":False}
