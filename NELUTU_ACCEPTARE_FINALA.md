# Neluțu — raport de acceptare înainte de lansare

**Ramură:** `nelutu-local-dialogue-launch-20261009`  
**PR:** https://github.com/profudeconta-sketch/catalog-online/pull/101  
**Decizie:** GO doar pentru testare locală controlată. NO-GO pentru integrare sau publicare.

## Confirmări tehnice automate
- Dialog educațional local cu continuitate limitată; fără model generativ și fără API extern.
- Rutarea existentă a întrebărilor despre portal are prioritate.
- Situațiile sensibile identificate de filtrele existente determină un răspuns serios și șterg contextul.
- Întrebările foarte lungi sunt limitate; mesajele sensibile au prioritate față de această limită.
- Interfața Streamlit experimentală este dezactivată implicit.
- Teste Streamlit AppTest: întrebări succesive, resetare, sesiuni independente, schimbarea temei, mesaj sensibil urmat de continuare.
- Teste de regresie pentru centrul de notificări.

## Încă nevalidate printr-o probă practică
- Pornirea reală într-un browser pe Windows, în mediu local izolat.
- Afișarea pe desktop și pe telefon, inclusiv butoane, text și scroll.
- Comportamentul în cazul reîncărcării paginii, întreruperii conexiunii și închiderii sesiunii.
- Revizuirea de către diriginte a formulărilor pedagogice și a mesajelor sensibile.
- Audit complet de confidențialitate, accesibilitate și securitate.
- Compatibilitatea de integrare cu aplicația părinților în mediul de producție.

## Regula de aur — porți de lansare
- [x] Prototipul rămâne în ramură experimentală, fără merge.
- [x] Nu există integrare în `app_parinti.py` și nu se scrie în Excel/JSON.
- [x] Nu este necesar API AI extern cu facturare.
- [ ] Proba practică locală și pe telefon a fost efectuată și documentată.
- [ ] Verificarea integrată a portalului real, fără date personale în test, a fost efectuată.
- [ ] Utilizatorul a aprobat explicit versiunea exactă pentru lansare.

**Nu modificați `main`, nu activați publicarea și nu introduceți date reale până când toate condițiile nevalidate sunt îndeplinite.**

Acest raport nu reprezintă aprobare de merge sau lansare.
