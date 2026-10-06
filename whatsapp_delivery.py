"""WhatsApp gratuit: construiește doar linkuri wa.me; nu folosește API și nu trimite automat."""
from __future__ import annotations
import os
import re
import urllib.parse

def normalize_ro_phone(value):
    raw=re.sub(r"[^0-9+]","",str(value or "").strip())
    if raw.startswith("0040"): raw="+40"+raw[4:]
    elif raw.startswith("40") and not raw.startswith("+"): raw="+"+raw
    elif raw.startswith("0"): raw="+40"+raw[1:]
    if not re.fullmatch(r"\+40\d{9}",raw):
        raise ValueError("Numărul de telefon nu are un format românesc valid.")
    return raw

def whatsapp_link(phone, message):
    """Returnează un link wa.me. Nu contactează WhatsApp/Meta și nu confirmă livrarea."""
    normalized=normalize_ro_phone(phone)
    body=str(message or "").strip()
    if not body:
        raise ValueError("Mesajul WhatsApp este gol.")
    digits=normalized.lstrip("+")
    return "https://wa.me/"+digits+"?text="+urllib.parse.quote(body, safe="")

def teacher_phone():
    value=str(os.environ.get("TEACHER_PHONE") or "").strip()
    try:
        import streamlit as st
        if hasattr(st,"secrets") and "TEACHER_PHONE" in st.secrets:
            value=value or str(st.secrets["TEACHER_PHONE"]).strip()
    except Exception:
        pass
    return normalize_ro_phone(value) if value else None
