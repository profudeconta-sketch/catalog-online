# A doua aplicație Streamlit — lansare sigură, fără Neon

**Scop:** pornirea separată a laboratorului Neluțu, fără modificarea aplicațiilor școlare.

## Configurare în Streamlit

- Repozitoriu: `profudeconta-sketch/catalog-online`
- Ramură: `feature/nelutu-gemini-safe-foundation`
- Main file path: `nelutu_neon_lab_preview.py`
- Nume distinct de `nelutu-ai-test`; nu modificați aplicațiile existente.
- Nu introduceți niciun secret sau DSN Neon în această etapă.
- Nu folosiți `requirements-nelutu-neon-lab.txt` pentru acest prim test: pagina de pornire are nevoie doar de Streamlit din `requirements.txt`.

## Criteriu de acceptare

Aplicația separată pornește și afișează mesajul «Laborator închis: accesul la baza de date este dezactivat». Nu există butoane de rezervare, apeluri Gemini sau acces la date școlare.

**Important:** o aplicație Streamlit Community Cloud cu URL diferit nu este automat privată. Înainte de orice conexiune Neon trebuie demonstrată o restricție reală de acces, compatibilă cu mediul ales. Bifarea unor flaguri în secrete nu constituie autentificare.

## Ulterior

Doar după verificarea accesului restricționat: instalarea driverului PostgreSQL în mediul de laborator, configurarea unui rol Neon strict limitat, testul de restart, testul multi-instanta și rollback. Nu se folosesc contul administrator Neon sau tabela reală `public.nelutu_gemini_budget`.

**Stare:** GO pentru pornirea paginii offline; NO-GO pentru conectarea Neon și pentru producție.
