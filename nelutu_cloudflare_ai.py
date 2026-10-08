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
from nelutu_ai_romanian import polish_romanian

DEFAULT_MODEL="@cf/qwen/qwen3-30b-a3b-fp8"
MAX_QUESTION=1200
MAX_RESPONSE=2200

SYSTEM_PROMPT = NELUTU_PERSONA

@dataclass(frozen=True)
class AIResult:
    text: str
    available: bool
    reason: str = ""

class AIUnavailable(Exception):
    pass

def generate(question,*,account_id="",api_token="",model=DEFAULT_MODEL,history=None,transport=None,max_output_tokens=None):
    """Returnează AIUnavailable fără rețea dacă nu există configurare sau eligibilitate."""
    if history is not None:
        raise AIUnavailable("history_not_allowed")
    if not approved_external_question(question):
        raise AIUnavailable("not_eligible")
    if not account_id or not api_token:
        raise AIUnavailable("not_configured")
    if not isinstance(account_id,str) or not isinstance(api_token,str):
        raise AIUnavailable("invalid_credentials")
    if not api_token.strip() or "\\r" in api_token or "\\n" in api_token:
        raise AIUnavailable("invalid_credentials")
    if not re.fullmatch(r"[a-zA-Z0-9_-]{8,64}",account_id):
        raise AIUnavailable("invalid_account")
    if model != DEFAULT_MODEL:
        raise AIUnavailable("invalid_model")
    token_limit = ExperimentalPolicy().max_output_tokens if max_output_tokens is None else max_output_tokens
    if type(token_limit) is not int or not 1 <= token_limit <= 1600:
        raise AIUnavailable("invalid_token_limit")
    url="https://api.cloudflare.com/client/v4/accounts/"+account_id+"/ai/run/"+model
    payload=json.dumps({"messages":external_messages(question,SYSTEM_PROMPT),"max_tokens":token_limit}).encode("utf-8")
    request=urllib.request.Request(url,data=payload,headers={
        "Authorization":"Bearer "+api_token,
        "Content-Type":"application/json",
    },method="POST")
    opener=transport or urllib.request.urlopen
    try:
        with opener(request,timeout=18) as response:
            body=response.read(131072)
        data=json.loads(body)
        if not isinstance(data,dict):
            raise AIUnavailable("invalid_response")
        result=data.get("result") or {}
        if not isinstance(result,dict):
            raise AIUnavailable("invalid_response")
        answer=result.get("response")
        choices=result.get("choices") or []
        if not isinstance(choices,list):
            raise AIUnavailable("invalid_response")
        if choices and not isinstance(choices[0],dict):
            raise AIUnavailable("invalid_response")
        if choices and choices[0].get("finish_reason") == "length":
            raise AIUnavailable("truncated_response")
        if not data.get("success",False) or not isinstance(answer,str) or not answer.strip():
            raise AIUnavailable("invalid_response")
        # Never present a cut-off sentence as a complete educational answer.
        if len(answer.strip()) > MAX_RESPONSE:
            raise AIUnavailable("oversized_response")
        return AIResult(polish_romanian(answer.strip()),True)
    except AIUnavailable:
        raise
    except (urllib.error.URLError,TimeoutError,OSError,ValueError,KeyError) as exc:
        raise AIUnavailable("provider_unavailable") from exc

def contract():
    return {"opt_in":True,"writes_student_data":False,"free_tier_only_not_guaranteed":True,"billing_must_be_disabled_or_capped":True,
            "external_processing_when_enabled":True,"forwards_student_records":False}
