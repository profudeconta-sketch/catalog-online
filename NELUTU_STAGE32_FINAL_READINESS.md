# Neluțu 2.0 — Etapa 32: verificare finală de compatibilitate și siguranță

Data verificării: 10 octombrie 2026. Domeniu: ramura experimentală `feature/nelutu-gemini-safe-foundation`; numai audit, fără integrare.

## Verificări confirmate
- Diferența față de `main`: 17 fișiere, toate aferente prototipului Neluțu, testelor sau auditului; fără schimbări în `app_web_catalog.py`, `app_parinti.py`, cataloage Excel/JSON ori fluxuri școlare.
- Pagina `nelutu_gemini_preview.py` este autonomă și nu importă aplicațiile școlare.
- Nouă acțiuni de rețea sunt condiționate în interfață de consimțământ și rezervarea încercării; testele offline aferente Etapei 31 au trecut.
- Patru scenarii de dialog fix sunt verificate exact la intrarea în `send_fixed_exchange`; conversațiile neaprobate sunt respinse înainte de rețea.
- `generate` refuză istoricul și cere activare/confirmare; codul nu expune cheia în interfață.
- Buget de test: trei încercări per sesiune și 12 per instanță, fără reîncercări automate. Sunt limite temporare, nu o cotă globală sau o garanție de cost.
- Testele GitHub pentru Etapa 31: `Nelutu offline regression tests` și `Notification center tests`, ambele `success` la commit `4893f0f`.

## Riscuri reziduale și condiții obligatorii înainte de producție
1. **Blocaj de confidențialitate:** `is_public_general_chat` este o euristică pe cuvinte-cheie/șabloane, nu un detector sigur de date personale. Nu este acceptabilă ca singura protecție pentru text liber în aplicații școlare.
2. **Limitare incompletă la nivel backend:** `generate` și `diagnose_status` acceptă orice text care trece euristica, dacă un apelant le activează și confirmă; lista exactă de mesaje fictive este impusă în UI și în transportul conversațiilor fixe, nu în aceste două funcții. Înainte de integrare, este necesar un control de rutare independent de UI.
3. **Cote nedurabile:** limitele în memorie se resetează la restart și nu acoperă multiple instanțe; configurarea unei cote la furnizor, monitorizarea și controlul cheii sunt obligatorii înainte de expunere publică.
4. **Politică și protecția datelor:** evaluare formală a datelor trimise către furnizor, a temeiului, a informării utilizatorilor, a retenției și a drepturilor de acces înainte de orice funcționalitate reală.
5. **Compatibilitate funcțională:** CI și inspecția codului nu înlocuiesc testarea cap-coadă pe copii anonimizate/ficționale ale fluxurilor profesor-părinte; nu se execută pe datele reale fără autorizare.
6. **Izolare operațională:** cheile, deploymentul și permisiunile pentru experiment trebuie să rămână separate de producție; niciun import, apel API sau scriere în catalog din prototip.

## Decizie
**PASS pentru demonstrație izolată, cu scenarii prestabilite și teste controlate. NO-GO pentru integrare în producție.**

Nu se face merge în `main`, nu se schimbă aplicațiile active și nu se transmit date reale către Gemini. Trecerea la producție necesită remedierea riscurilor, dovezi de test și aprobare explicită.
