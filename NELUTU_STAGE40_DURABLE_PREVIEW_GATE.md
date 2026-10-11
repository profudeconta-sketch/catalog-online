# Etapa 40 — integrare experimentală opțională a bugetului persistent

- Demo-ul separat acceptă opțional două setări Streamlit Secrets: NELUTU_DURABLE_BUDGET_ENABLED = true și NELUTU_DURABLE_BUDGET_PATH = "/cale/absoluta/dedicata/budget.sqlite3".
- Valoarea implicită este false: demo-ul actual continuă cu limitarea anterioară pe sesiune și pe proces.
- În modul persistent, fiecare încercare necesită rezervare în SQLite înainte de contorul de sesiune/proces și înainte de cererea către Gemini. Lipsa sau epuizarea bazei de date blochează cererea.
- Un eșec ulterior rezervării nu rambursează încercarea, ca măsură conservatoare.
- Nu configurați fișierul în depozitul de date școlare, în directorul catalogului sau pe disc efemer. Dacă infrastructura nu oferă volum persistent comun, modul nu trebuie activat.
- SQLite pe un volum partajat între instanțe are limitări operaționale; pentru integrare reală multi-instance este necesar un serviciu tranzacțional centralizat, cu monitorizare și controlul accesului.
- Nu au fost efectuate apeluri reale Gemini și nu au fost schimbate aplicațiile școlare.
- Nu sunt autorizate merge în main, date școlare, facturare sau dialog liber.

Verdict: integrare tehnică demonstrativă, dezactivată implicit; validarea CI și configurarea infrastructurii sunt condiții separate.
