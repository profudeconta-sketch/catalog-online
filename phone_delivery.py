"""Livrare SMS optionala. Nu contine credențiale sau numere hardcodate."""
from __future__ import annotations
import base64, json, os, re, urllib.parse, urllib.request

class PhoneDeliveryError(RuntimeError): pass

def _secret(name):
    value=os.environ.get(name) or ""
    try:
        import streamlit as st
        if hasattr(st,"secrets") and name in st.secrets:
            value=value or str(st.secrets[name])
    except Exception:
        pass
    return str(value).strip()

def normalize_ro_phone(value):
    raw=re.sub(r"[^0-9+]","",str(value or "").strip())
    if raw.startswith("0040"): raw="+40"+raw[4:]
    elif raw.startswith("40") and not raw.startswith("+"): raw="+"+raw
    elif raw.startswith("0"): raw="+40"+raw[1:]
    if not re.fullmatch(r"\+40\d{9}",raw):
        raise ValueError("Numărul de telefon nu are un format românesc valid.")
    return raw

def sms_configured():
    return all(_secret(x) for x in ("TWILIO_ACCOUNT_SID","TWILIO_AUTH_TOKEN","TWILIO_FROM_NUMBER"))

def send_sms(to_phone, body):
    to_phone=normalize_ro_phone(to_phone)
    body=str(body or "").strip()
    if not body: raise ValueError("Mesajul SMS este gol.")
    sid=_secret("TWILIO_ACCOUNT_SID"); token=_secret("TWILIO_AUTH_TOKEN"); sender=_secret("TWILIO_FROM_NUMBER")
    if not sid or not token or not sender:
        raise PhoneDeliveryError("Serviciul SMS nu este configurat.")
    url=f"https://api.twilio.com/2010-04-01/Accounts/{urllib.parse.quote(sid,safe='')}/Messages.json"
    data=urllib.parse.urlencode({"To":to_phone,"From":sender,"Body":body}).encode("utf-8")
    auth=base64.b64encode(f"{sid}:{token}".encode()).decode()
    req=urllib.request.Request(url,data=data,method="POST",headers={
        "Authorization":f"Basic {auth}","Content-Type":"application/x-www-form-urlencoded",
        "User-Agent":"CatalogOnlineIXTH/1.0",
    })
    try:
        with urllib.request.urlopen(req,timeout=10) as resp:
            payload=json.loads(resp.read().decode("utf-8"))
    except Exception as ex:
        raise PhoneDeliveryError("Livrarea SMS nu a fost confirmată.") from ex
    msg_sid=str(payload.get("sid") or "").strip()
    if not msg_sid: raise PhoneDeliveryError("Furnizorul SMS nu a returnat confirmarea mesajului.")
    return {"provider":"twilio","message_sid":msg_sid,"status":str(payload.get("status") or "accepted")}


def teacher_phone():
    value=_secret("TEACHER_PHONE")
    return normalize_ro_phone(value) if value else None
