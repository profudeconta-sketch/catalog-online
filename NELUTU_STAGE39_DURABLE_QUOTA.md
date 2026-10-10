# Etapa 39 — contor persistent Gemini (prototip offline)

Implementare izolată: nelutu_durable_budget.py; teste: test_nelutu_durable_budget.py.

- SQLite, tranzacție BEGIN IMMEDIATE și UPDATE condițional: rezervare atomică pentru procese care folosesc același fișier pe un sistem de fișiere persistent.
- Maxim 12 încercări totale per registru; fără reset automat, fără refund, fără apeluri Gemini.
- Dacă fișierul lipsește sau nu poate fi deschis în siguranță, rezervarea este respinsă.
- Necesită cale absolută, dedicată, în afara fișierelor catalogului. Nu stochează mesaje, date personale, chei API sau informații școlare.

**Nu este conectat încă la butoanele Streamlit**. Demo-ul existent continuă să folosească limita de 3/sesiune și 12/proces; integrarea contorului persistent necesită alegerea și configurarea explicită a unei stocări durabile separate. SQLite pe disc local efemer nu oferă persistență după redeploy și nici limită globală între instanțe distribuite.

Criterii pentru următoarea etapă: validarea testelor, stabilirea locației persistente, un singur punct de rezervare înainte de fiecare apel și fail-closed la lipsa configurației. Cheia Gemini trebuie limitată suplimentar în consola furnizorului.

Verdict: componentă experimentală, nu integrare în aplicațiile școlare.
