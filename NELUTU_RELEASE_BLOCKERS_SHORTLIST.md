# Neluțu — plan scurt de închidere pentru lansare

**Status:** fundația experimentală este validată offline; lansarea în producție NU este aprobată.

## Nu repetăm

- Testul local Neon cu 8 cereri concurente: 3 acceptate, 5 refuzate, 0 erori.
- Testele Streamlit cu date fictive: memorie, izolare sesiuni, erori 429/503/rețea.
- Testele GitHub Actions pentru componentele experimentale.

## Blocaje reale, fără dezvoltări suplimentare nejustificate

1. **Mediu privat de test:** aplicația publică `nelutu-ai-test` nu este potrivită pentru un control de rezervări de laborator. Se verifică mai întâi posibilitatea restricționării accesului sau a unui mediu privat distinct.
2. **Persistență cloud:** contorul izolat trebuie conectat numai cu rol de test, iar starea trebuie să supraviețuiască repornirii.
3. **Cotă globală:** două sesiuni/instanțe trebuie să respecte împreună plafonul, cu erori care blochează apelurile.
4. **Rollback:** dezactivarea componentei experimentale trebuie demonstrată fără impact asupra aplicațiilor școlare.
5. **Cost și confidențialitate:** verificare explicită a condițiilor actuale ale furnizorului, limitelor gratuite, prelucrării datelor și absenței cheilor expuse.
6. **Interfață finală și acord:** test desktop/mobil și aprobare explicită pentru integrarea controlată.

## Regula de aur

- Fără modificări în `app_web_catalog.py`, `app_parinti.py`, catalog Excel/JSON, secrete sau `main` în această etapă.
- Fără conectare la Gemini, fără date școlare reale, fără costuri neautorizate.
- Niciun rezultat offline nu se declară drept dovadă de producție.
- Fără merge automat al PR #112.

## Decizie

**GO** pentru finalizarea validării de laborator; **NO-GO** pentru lansare până la demonstrarea blocajelor de mai sus.
