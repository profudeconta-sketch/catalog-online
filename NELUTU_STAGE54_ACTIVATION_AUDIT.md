# Etapa 54 — Auditul condițiilor de activare Neluțu 2.0

## Stare: NO-GO pentru portalul școlar

Etapele 49–53 au verificări automate verzi pe ramura experimentală. Acest rezultat dovedește numai comportamentul testelor izolate, nu siguranța integrării într-o aplicație reală.

### Condiții obligatorii înaintea activării
1. **Interfață unică:** se păstrează mascota, butonul și formularul existente. Nu se introduce o a doua casetă.
2. **Comutator Gemini separat:** implicit dezactivat; nu se reutilizează `NELUTU_V2_ENABLED`, care controlează răspunsurile locale existente.
3. **Confidențialitate:** revizuire explicită a textelor trimise, a consimțământului și a datelor personale; filtrul de demonstrație acceptă numai mesaje fictive aprobate exact. Niciun context școlar sau răspuns local nu se transmite.
4. **Cotă durabilă:** demonstrarea unui spațiu de stocare persistent între reporniri și instanțe, separat de fișierele școlare; cota SQLite nu este suficientă dacă stocarea Streamlit este efemeră.
5. **Cheie și costuri:** verificarea secretelor, limitelor și politicii de facturare ale furnizorului; niciun apel real în testele offline.
6. **Revenire:** test end-to-end cu comutator OFF, eșec provider, eroare locală, quota epuizată, răspuns invalid și restart.
7. **Protecția sistemului:** backup și verificare de diferențe; fără modificări la Excel, JSON, aplicațiile live ori la `main` înaintea unei aprobări distincte.
8. **Aprobare finală:** accept explicit pentru schimbarea punctuală în aplicația live, după trecerea tuturor condițiilor.

### Concluzie
Nu se activează Gemini în portal. Următoarea etapă este un plan de conectare reversibilă, cu o singură interfață, fără schimbări în producție.
