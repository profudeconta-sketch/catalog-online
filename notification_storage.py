"""Registru separat pentru notificari si inbox.

Nu modifica Excelul si nu schimba registrele-sursa. Evenimentele sunt idempotente
dupa (recipient, event_type, source_type, source_id, source_revision).
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from document_storage import DOCUMENT_ROOT, DocumentConflictError, DocumentStorageError, load_registry, private_read, private_write
from leave_pass_storage import load_leave_pass_registry

NOTIFICATION_REGISTRY_PATH=f"{DOCUMENT_ROOT}/registru_notificari.json"
RECIPIENT_TEACHER="DIRIGINTE"
RECIPIENT_PARENT="PARINTE"

def _event_id(recipient,event_type,source_type,source_id,source_revision=""):
    raw="|".join(map(str,(recipient,event_type,source_type,source_id,source_revision)))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

def load_notification_registry():
    raw,sha=private_read(NOTIFICATION_REGISTRY_PATH)
    if raw is None:
        return {"schema_version":1,"events":[]},None
    try: data=json.loads(raw.decode("utf-8"))
    except Exception as ex: raise DocumentStorageError("Registrul notificărilor este invalid.") from ex
    if data.get("schema_version")!=1 or not isinstance(data.get("events"),list):
        raise DocumentStorageError("Structura registrului notificărilor este invalidă.")
    return data,sha

def save_notification_registry(registry,expected_sha):
    if registry.get("schema_version")!=1 or not isinstance(registry.get("events"),list):
        raise DocumentStorageError("Registrul notificărilor nu poate fi salvat.")
    raw=json.dumps(registry,ensure_ascii=False,indent=2,sort_keys=True).encode("utf-8")
    return private_write(NOTIFICATION_REGISTRY_PATH,raw,expected_sha=expected_sha,message="Actualizare registru notificari")

def ensure_notification(*,recipient,event_type,source_type,source_id,student_key,
                        source_revision="",title="",message="",created_at_utc=None):
    eid=_event_id(recipient,event_type,source_type,source_id,source_revision)
    for _ in range(3):
        registry,sha=load_notification_registry()
        matches=[x for x in registry["events"] if x.get("id")==eid]
        if len(matches)>1: raise DocumentConflictError("Evenimentul de notificare este duplicat.")
        if matches: return dict(matches[0]),False
        event={
            "id":eid,"schema_version":1,"recipient":str(recipient),"event_type":str(event_type),
            "source_type":str(source_type),"source_id":str(source_id),"source_revision":str(source_revision or ""),
            "student_key":str(student_key),"title":str(title),"message":str(message),
            "created_at_utc":created_at_utc or dt.datetime.now(dt.timezone.utc).isoformat(),
            "read_at_utc":None,"delivery_status":"PENDING","delivered_at_utc":None,
        }
        registry["events"].append(event)
        try:
            save_notification_registry(registry,sha); return dict(event),True
        except DocumentConflictError: continue
    raise DocumentConflictError("Notificarea nu a putut fi înregistrată în siguranță.")

def list_notifications(*,recipient,unread_only=False,student_key=None):
    registry,_=load_notification_registry()
    out=[]
    for x in registry["events"]:
        if x.get("recipient")!=recipient: continue
        if unread_only and x.get("read_at_utc"): continue
        if student_key is not None and x.get("student_key")!=str(student_key): continue
        out.append(dict(x))
    return sorted(out,key=lambda x:x.get("created_at_utc",""),reverse=True)

def mark_notification_read(event_id,recipient):
    for _ in range(3):
        registry,sha=load_notification_registry()
        matches=[x for x in registry["events"] if x.get("id")==str(event_id) and x.get("recipient")==recipient]
        if len(matches)!=1: raise DocumentStorageError("Notificarea nu există pentru destinatar.")
        event=matches[0]
        if event.get("read_at_utc"): return dict(event),False
        event["read_at_utc"]=dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            save_notification_registry(registry,sha); return dict(event),True
        except DocumentConflictError: continue
    raise DocumentConflictError("Citirea notificării nu a putut fi confirmată.")


def reconcile_teacher_inbox():
    """Derivă idempotent Inbox-ul din sursele primare; nu modifică sursele."""
    docs,_=load_registry()
    leaves,_=load_leave_pass_registry()
    created=0
    for item in docs.get("documents",[]):
        if item.get("direction")!="PARINTE_SCOALA":
            continue
        _,was_created=ensure_notification(
            recipient=RECIPIENT_TEACHER,event_type="DOCUMENT_PARINTE",source_type="DOCUMENT",
            source_id=item.get("id"),student_key=item.get("student_key"),
            title="Document nou de la părinte/reprezentant legal",
            message="A fost primit un document nou în Portalul Părinților.",
            created_at_utc=item.get("created_at_utc"),
        )
        created+=int(was_created)
    for item in leaves.get("requests",[]):
        _,was_created=ensure_notification(
            recipient=RECIPIENT_TEACHER,event_type="CERERE_INVOIRE",source_type="INVOIRE",
            source_id=item.get("id"),source_revision=item.get("revision",1),
            student_key=item.get("student_key"),
            title="Cerere de învoire nouă",
            message="A fost primită o cerere de învoire care necesită verificare.",
            created_at_utc=item.get("transmitted_at_utc"),
        )
        created+=int(was_created)
    return created
