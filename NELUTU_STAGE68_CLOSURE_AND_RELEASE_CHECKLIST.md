# Neluțu 2.0 — Etapa 68: bilanț de închidere a dezvoltării izolate

Data: 2026-10-10. Ramura: `feature/nelutu-gemini-safe-foundation`, draft PR #112.

## Verdict separat

**GO pentru încheierea dezvoltării fundamentului experimental offline**, pe baza celor patru fluxuri CI verzi la commitul `aef77142a40f64307a12a5c5f38a1e9b2576cc5f`. Aceasta NU reprezintă aprobare pentru conectarea la aplicațiile școlare.

**NO-GO pentru integrarea Gemini în producție, merge în main și transmiterea datelor școlare.** Nicio aprobare pentru aceste acțiuni nu rezultă din continuarea testelor.

## Dovezi existente

- Etapele 61–67: teste pentru erori de cote, stocare deteriorată/indisponibilă, revenire locală, indicatori boolean stricți și respingere fără apel extern sau consum de cotă.
- Un singur formular Neluțu în portal, conform contractelor statice; adaptorul experimental nu este importat în aplicațiile active.
- Textul trimis în demonstrația de integrare este limitat la mesaje fictive aprobate exact; răspunsul local și contextul școlar nu sunt trimise.
- Patru fluxuri GitHub Actions verzi pentru Etapa 67. Acestea sunt teste automatizate, nu teste live de infrastructură.

## Dovezi externe încă lipsă

1. **Stocare persistentă între restarturi**: demonstrație pe infrastructura de test, cu volum dedicat care supraviețuiește restartului, fără a utiliza fișierele catalogului.
2. **Cotă comună între instanțe**: test real cu două instanțe care folosesc același mecanism de rezervare atomică. Dacă Streamlit Cloud nu oferă stocare comună durabilă, se cere backend dedicat; SQLite local nu este suficient.
3. **Furnizor**: revizuirea termenilor, retenției, tarifelor, limitelor și restricțiilor cheii; fără publicarea secretelor.
4. **Confidențialitate**: aprobarea explicită a politicii și a consimțământului pentru orice text care ar urma să fie transmis.
5. **UI E2E**: verificare reală desktop și mobil a mascotei, unui singur popover/formular/răspuns, fără a doua interfață.
6. **Rollback E2E**: comutator Gemini distinct, implicit OFF, eșec furnizor, cotă epuizată, restart; `NELUTU_V2_ENABLED` rămâne comutatorul local.
7. **Aprobare explicită de producție**: doar după cele șase verificări precedente, pentru o schimbare precis delimitată.

## Procedură practică de validare, fără atingerea producției

- Se pregătește o instanță separată de test, cu date fictive și stocare persistentă dedicată; nu se reutilizează registrul privat al elevilor.
- Se rezervă o încercare, se repornește instanța și se verifică faptul că numărul folosit nu scade; se repetă din două instanțe simultan și se verifică limita globală.
- Se simulează stocare indisponibilă, furnizor indisponibil și dezactivarea integrării: toate trebuie să blocheze ieșirea externă și să lase răspunsul local utilizabil.
- Se inspectează manual UI pe desktop și mobil, fără date reale, și se consemnează dovezile.
- Dacă oricare verificare eșuează, verdictul rămâne NO-GO. Nu se activează Gemini în portal și nu se face merge în main.

## Criteriul de închidere

Fundamentul experimental poate fi declarat **finalizat pentru testele offline**, dar proiectul complet Neluțu 2.0 **nu este gata de lansare** până la verificarea infrastructurii, a confidențialității și a UI-ului live. Nu se inventează dovezi sau un verdict pozitiv pentru producție.


## Etapa 69 — verificare de lansare după regresiile PostgreSQL/Neon

Commitul `ba51d3038a05c9c746b0b3101ad76b72e874e77a` are opt fluxuri GitHub Actions finalizate cu succes. Acest rezultat demonstrează numai comportamentele testate automat, nu validarea infrastructurii de producție.

### Dovezi încă obligatorii pentru GO de producție

- Test end-to-end într-un mediu Streamlit separat, cu date exclusiv fictive, pe desktop și mobil, inclusiv revenirea la Neluțu local
- Confirmarea persistenței și a cotei comune între instanțe după restart și întreruperi, fără conectare la fișierele școlare
- Verificarea termenilor, limitelor și costurilor furnizorului, cu mecanism verificabil pentru cost zero
- Evaluare de confidențialitate și autorizare explicită a oricărei transmiteri externe; implicit fără date școlare
- Plan de rollback testat și verificare că funcționalitățile profesorilor/părinților rămân identice
- Aprobare explicită, separată, pentru schimbarea exactă propusă în producție

**Verdict Etapa 69:** GO pentru baza experimentală offline; **NO-GO pentru merge, conectare Gemini sau lansare** până la completarea tuturor dovezilor externe. PR #112 rămâne Draft. Niciun rezultat CI nu poate substitui aprobarea de producție.
