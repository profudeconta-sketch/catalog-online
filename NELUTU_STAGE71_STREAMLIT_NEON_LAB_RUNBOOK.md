# Etapa 71 — protocol pentru persistența izolată Streamlit–Neon

**Stare: NEEXECUTAT în cloud.** Acest document nu autorizează lansarea în producție.

## Dovezi deja obținute (nu se repetă inutil)

- Test local Neon: 8 cereri simultane, 3 acceptate, 5 refuzate, 0 erori; rolul experimental a fost dezactivat și tabelul test a fost eliminat.
- Simulări Streamlit: memorie și sesiuni izolate, 429/503/rețea, contor de instanță.
- GitHub Actions: verificări offline pentru izolarea rolului și contorul experimental.

Acestea **nu** dovedesc persistența Streamlit–Neon după restart sau între instanțe.

## Izolare obligatorie

1. Se folosește numai schema `nelutu_test_concurenta` și tabelul `nelutu_streamlit_lab_budget`; niciodată `public.nelutu_gemini_budget`.
2. Aplicația de laborator rămâne separată de `app_web_catalog.py` și `app_parinti.py`.
3. Rolul runtime `nelutu_test_runner` trebuie să aibă numai USAGE pe schema izolată și SELECT/UPDATE pe tabelul izolat, fără CREATE/DROP și fără drepturi pe catalog sau bugetul Gemini.
4. **Nu se pune DSN de administrator în Streamlit.** Nicio parolă sau DSN nu se copiază în GitHub, chat, loguri sau capturi.
5. Orice eroare de conectare sau permisiuni blochează rezervarea. Nicio cerere către Gemini.
6. Deoarece aplicația de test este publică, nu se adaugă butonul de consum al cotei până când accesul la test nu este restricționat sau testul nu este mutat într-un mediu privat.
7. Nu se execută DDL din aplicație. Administratorul creează separat tabelul, cu aprobare explicită, și verifică proprietarul și privilegiile.

## Teste necesare, în ordine

1. Test offline pentru configurație invalidă, acces la tabelul real interzis, erori DB și atomicitate.
2. Verificare numai în citire a rolului de laborator, fără acces la tabelul bugetului real.
3. Conectare la tabelul izolat dintr-un mediu de test cu acces restricționat; se confirmă contorul inițial și exact o rezervare fictivă.
4. Restart al **aplicației experimentale**, nu al aplicațiilor școlare; se confirmă că valoarea rămâne neschimbată.
5. Două sesiuni/instanțe independente: nu depășesc plafonul global de 3.
6. Întreruperea conexiunii: rezervarea este refuzată, fără apel extern.
7. Rollback: se dezactivează integrarea, se confirmă revenirea la modul local și se verifică faptul că aplicațiile școlare nu sunt afectate.
8. Se revizuiesc explicit confidențialitatea, condițiile furnizorului, costurile și acordul final de producție.

## Criteriu GO

Numai după dovezi reale pentru toate punctele și aprobare separată pentru integrarea în `main`.
Până atunci: **GO pentru laborator; NO-GO pentru producție**.
