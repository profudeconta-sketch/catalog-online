# Etapa 43 — condiții de activare și integrare (audit fără schimbări operaționale)

Data: 2026-10-10. Ramură: feature/nelutu-gemini-safe-foundation.

## Dovezi
- Commit 0247a92c2f34c9b6106d56588baaf989a3e1188f: toate cele trei workflow-uri GitHub au success, inclusiv testele SQLite multiproces și după repornire.
- Compararea cu main arată numai fișiere experimentale, documentație, teste și workflow-ul separat; nu sunt schimbate fișierele aplicațiilor școlare.
- Modul persistent în nelutu_gemini_preview.py este opt-in, activ numai dacă NELUTU_DURABLE_BUDGET_ENABLED este boolean true. Calea se citește din NELUTU_DURABLE_BUDGET_PATH.
- În lipsa unei configurații valide, rezervările sunt blocate când modul persistent este activ.

## Blocaje reale rămase
1. Nu există o dovadă că mediul Streamlit Cloud oferă un volum persistent și partajat; SQLite local poate dispărea la redeploy. Nu activați modul persistent pe stocare efemeră.
2. Limitele de consum și facturarea furnizorului Google trebuie confirmate din contul administrat de utilizator; nu sunt verificate prin teste offline.
3. Cheia trebuie izolată, restricționată și monitorizată; nu se partajează în conversație și nu se scrie în repository.
4. O integrare școlară reală necesită evaluare de confidențialitate, temei legal, minimizarea datelor și un gateway separat; allowlist-ul actual permite numai prompturi fictive.
5. Pentru trafic distribuit, este necesar un contor tranzacțional centralizat, nu o presupunere despre disc local comun.
6. Este necesar un plan de rollback, testare E2E într-un mediu fără date reale și aprobarea explicită a integrării.

## Decizie
PASS: prototip demonstrativ offline izolat.
BLOCKED: activare persistentă reală până la verificarea stocării; dialog liber și integrare în aplicațiile școlare până la rezolvarea tuturor blocajelor.

Nu se modifică Streamlit Secrets, nu se fac apeluri Gemini, nu se activează billing și nu se face merge în main.
