# Etapa 47 — auditul punctelor de integrare existente

Data: 2026-10-10. Audit numai în ramura experimentală.

## Puncte reale observate
- `app_parinti.py` importă `nelutu_parent_guide.answer_parent` și `nelutu_dialogue_adapter.answer_parent_dialogue`.
- `app_parinti.py` are deja comutatorul `NELUTU_V2_ENABLED`, cu fallback la asistentul clasic; acesta este un comutator pentru dialogul local existent, **nu** pentru Gemini.
- `app_parinti.py` folosește st.session_state pentru `nelutu_v2_dialogue_state`.
- `app_web_catalog.py` folosește `nelutu_mascot` pentru mascote și sugestii vizuale.
- `nelutu_assistant.py` implementează asistentul local read-only pentru părinți, inclusiv tratarea subiectelor sensibile.
- `nelutu_optional_integration_adapter.py` este izolat și dezactivat implicit. Nu este importat de aplicațiile școlare.

## Principiul de integrare recomandat
Nu se reutilizează `NELUTU_V2_ENABLED` pentru Gemini. Este necesar un comutator separat, dezactivat implicit, cu verificări suplimentare înainte de orice apel extern. Nicio întrebare contextualizată cu informații despre elev, părinte, note, absențe, documente sau identificatori nu trebuie trimisă către furnizorul AI. În absența unei aprobări de confidențialitate și a infrastructurii verificate, Neluțu local rămâne singura cale operațională.

## Status
PASS: verificarea punctelor de integrare și izolarea codului experimental.
BLOCKED: conectarea efectivă la portal, activarea Gemini și utilizarea în producție. Sunt necesare aprobare explicită separată, plan de rollback, teste E2E și infrastructură persistentă confirmată.

Nu s-au modificat `app_parinti.py`, `app_web_catalog.py`, fișierele de date sau secretele.
