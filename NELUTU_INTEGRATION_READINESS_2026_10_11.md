# Neluțu — audit de integrare reală (11 octombrie 2026)

## Dovezi confirmate
- Testul real local Neon de concurență este deja trecut: 8 solicitări, 3 acceptate, 5 refuzate, 0 erori; tabelul temporar eliminat și rolul dezactivat la finalul testului inițial. Sursă: NELUTU_STAGE71_STREAMLIT_NEON_LAB_RUNBOOK.md. **NU SE REPETĂ** testul deja validat.
- Simulările offline Streamlit pentru sesiuni izolate, erori 429/503/rețea și contor de instanță sunt consemnate în Etapa 71. **NU SE REPETĂ** fără o schimbare relevantă de cod.

- Utilizatorul a verificat în Streamlit că rolul de test se autentifică în Neon, are USAGE și CREATE pe schema izolată și nu are privilegiile testate pe tabelul bugetului real.
- Opt fluxuri GitHub Actions verzi la commitul 33bad2e413a40122be4b2613a1ec2bd53a452590.
- PR #112 este Draft, neintegrat în main.
- Nu s-au executat apeluri reale Gemini în această etapă.

## Blocaj critic: două modele incompatibile de permisiuni
- nelutu_neon_concurrency_probe.py creează și șterge un tabel efemer din schema izolată. Acesta cere CREATE pentru rolul de runtime.
- NELUTU_STAGE71_STREAMLIT_NEON_LAB_RUNBOOK.md interzice explicit CREATE/DROP pentru rolul runtime și cere ca administratorul să creeze separat tabelul persistent.
- Confirmarea dreptului CREATE este o verificare de conectivitate, **nu** o aprobare de a rula un test cu scrieri.
- Aplicația de test este publică; runbook-ul interzice activarea butonului de consum al cotei până la restricționarea accesului.

## Decizie de siguranță
- NU se activează testul de concurență cu scrieri în aplicația publică.
- NU se folosesc credențiale neondb_owner în Streamlit.
- NU se folosesc date școlare, bugetul real sau apeluri Gemini.
- Înaintea testului persistent: rol runtime cu privilegii minime (USAGE + SELECT/UPDATE doar pe tabelul izolat), tabel creat separat de administrator, acces la test restricționat, verificare atomicitate și cleanup/rollback.
- Proba efemeră cu CREATE/DROP poate fi rulată numai într-un laborator privat, cu aprobare distinctă, fără date reale și cu verificarea curățării.

## Criterii încă neîndeplinite pentru GO de producție
1. Dovadă distinctă de cotă persistentă **Streamlit–Neon** după restart și în două instanțe (nu se confundă cu testul local Neon de concurență deja trecut).
2. Test de eroare Neon / rollback și revenire locală.
3. Test UI E2E desktop și mobil în interfața unică.
4. Revizuirea costurilor și condițiilor furnizorului, a confidențialității și a transmiterii externe.
5. Revizuire precisă a modificărilor necesare în aplicațiile active, cu backup și plan de revenire.
6. Aprobare explicită și separată a integrării în main.

**Verdict: GO pentru dezvoltare și verificări offline; NO-GO pentru integrarea reală în producție.**

## Registru anti-retestare — obligatoriu înaintea fiecărei etape

| Verificare | Dovadă | Stare | Acțiune |
|---|---|---|---|
| Neon concurență locală 8/3/5 | Etapa 71 | TRECUT | Nu repeta |
| Simulări 429/503/rețea | Etapa 71 | TRECUT offline | Nu repeta fără modificări relevante |
| Rol Neon și izolare read-only | Confirmare utilizator în Streamlit, 11.10 | TRECUT | Nu repeta |
| CREATE în schema izolată | Confirmare utilizator în Streamlit, 11.10 | TRECUT | Nu repeta; nu autorizează scrieri |
| CI 8 workflow-uri | SHA 33bad2e | TRECUT | Verifică doar commituri noi |
| Persistență Streamlit–Neon după restart | Nicio dovadă de execuție în Etapa 71 | NECONFIRMAT | Caută dovezi ulterioare înainte de test |
| Două instanțe Streamlit–Neon | Nicio dovadă de execuție în Etapa 71 | NECONFIRMAT | Caută dovezi ulterioare înainte de test |
| UI E2E desktop și mobil | Nicio dovadă în documentele consultate | NECONFIRMAT | Audit istoric înainte de retest |

Regulă: înainte de a propune orice test, se caută întâi dovezile din istoricul GitHub și conversații. „Neconfirmat” nu înseamnă „neexecutat”.

## Audit de cablare reală — 11.10, fără reluarea testelor trecute

Cod inspectat: `nelutu_preview_deploy/app.py`, `nelutu_gemini_preview.py`, `nelutu_streamlit_lab_budget.py`, `nelutu_streamlit_lab_gate.py`, `nelutu_optional_integration_adapter.py`, `nelutu_unified_orchestrator.py`.

**Constatare verificabilă:** entrypoint-ul Streamlit lansează `nelutu_gemini_preview.py` și apoi afișează diagnosticul read-only Neon. Funcția `reserve_gemini_attempt()` din preview folosește `DurableBudget` (mod SQLite opt-in), `DemoBudget` și `InstanceBudget`; nu utilizează `IsolatedLabBudget` și nici `lab_reserve()`. Prin urmare, succesul diagnosticului Neon nu înseamnă că bugetul Gemini este deja cablat la Neon. Nu se afirmă contrariul.

**Limitare suplimentară:** `nelutu_integration_gate.py` permite doar întrebări publice demonstrative prestabilite. Aceasta nu demonstrează dialogul generativ liber solicitat pentru producție. `nelutu_unified_orchestrator.py` are callback opțional, dar nu constituie dovada integrării în portal.

**Ordinea corectă, fără teste duplicate:** (a) păstrarea dovezilor Neon 8/3/5 și CI; (b) proiectarea separată a conexiunii la contorul persistent cu rol minim și acces privat; (c) teste strict noi pentru persistență/restart și integrare reală; (d) validarea confidențialității, a costurilor și UI; (e) acord explicit pentru modificările în aplicația activă.

**Verdict tehnic:** fundament experimental verificat parțial, dar cablarea persistentă Streamlit–Neon în fluxul de răspuns și dialogul liber în portal nu sunt implementări demonstrate de codul inspectat. Nu se face merge și nu se activează furnizorul.

## Corecție audit: comutatoare existente și cale Neon reală în preview

După verificarea liniilor 555–650 din `nelutu_gemini_preview.py`, constatarea anterioară „Neon nu este legat de fluxul experimental Gemini” era prea generală. **Există deja o cale de dialog liber care rezervă buget prin `PostgreSQLBudget(NELUTU_NEON_DSN).reserve()`**, cu comutatoare stricte `NELUTU_NEON_BUDGET_ENABLED`, `NELUTU_UNIFIED_LIVE_ENABLED`, `NELUTU_NEON_LIVE_BUDGET_APPROVED`, cod de operator `NELUTU_UNIFIED_ACCESS_CODE` și consimțământ explicit. Nu se reconstruiește.

Separat, demo-urile prestabilite din partea superioară a preview-ului folosesc `DurableBudget` SQLite și limite de sesiune/instanță. Acestea sunt fluxuri distincte și nu trebuie confundate. `NELUTU_TEST_DATABASE_URL` este numai pentru diagnosticul izolat; nu se confundă cu `NELUTU_NEON_DSN`, care indică bugetul PostgreSQL al fluxului generativ și necesită aprobare explicită pentru rezervare.

Nu există dovadă în cod că aceste comutatoare sunt activate în Streamlit Secrets; simpla prezență în surse nu autorizează apeluri reale Gemini sau scrieri în buget. Nici codul de operator al preview-ului nu se transferă părinților. Integrarea finală trebuie să păstreze o singură interfață și fără cod suplimentar pentru părinți.

**Regulă anti-duplicare:** înainte de a declara lipsă o funcționalitate, inspectăm întregul entrypoint, inclusiv secțiunile de la final, plus comutatoarele și testele istorice.

## Etapă de întărire a protecției cotei — 11.10

- În `nelutu_postgres_budget.py`, UPDATE condițional respinge explicit `used < 0`; `remaining()` respinge valori negative, peste limită și tipuri invalide. Testele de regresie au fost extinse în `test_nelutu_postgres_transactions.py`.
- Modificările sunt izolate pe ramura experimentală, fără DDL, fără conexiuni live, fără Gemini și fără modificarea aplicațiilor școlare.
- **Testele GitHub pentru noul commit trebuie confirmate separat**; rezultatele verzi pentru commituri anterioare nu certifică automat modificarea curentă.
- Criteriu GO de integrare: CI nou verde + dovezi E2E lipsă + confidențialitate/costuri + rollback + acord explicit. Până atunci: NO-GO pentru producție.
