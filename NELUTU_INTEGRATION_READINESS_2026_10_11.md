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
