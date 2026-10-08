# Neluțu — decizie de lansare controlată

Data evaluării: 2026-10-09.

## Confirmat
- GitHub Actions offline #22: SUCCESS, conform capturii utilizatorului, pentru revizia experimentală 067b02805a211737a06ff4782b9b5b39de89a01b.
- Aplicația existentă a părinților nu a fost modificată prin prototipul extern.
- Protecții testate offline: allowlist pentru întrebări publice, refuzul istoricului, limite de răspuns și refuzul marcajelor <think>.
- Nicio probă LIVE suplimentară și nicio activare a serviciului extern în această etapă.

## Blocaje reale pentru lansarea AI extern
1. Nu există dovadă a unei limite de facturare impuse de furnizor care să garanteze zero lei. Limita de cereri pe sesiune nu este suficientă.
2. Dialogul generativ cu istoric nu este implementat: istoricul este respins pentru protecția datelor.
3. Evaluarea umană completă a conversațiilor, a limbii române și a cazurilor sensibile nu este finalizată.
4. Nu există validare de staging cu regresie pe ambele aplicații și procedură de revenire verificată.
5. Comparația GitHub main...nelutu-cloudflare-ai-prototype-20261008 arată ramuri divergente (147 commituri înainte, 27 în urmă); un merge integral nu este sigur fără reconciliere.

## Decizie
**NO-GO pentru activarea AI extern și merge integral în producție.**

**GO pentru continuarea funcționării versiunii existente a lui Neluțu**, fără activarea experimentală, fără costuri suplimentare și fără schimbarea datelor primare.

## Pașii rămași
- Confirmarea zero-cost la nivelul furnizorului sau renunțarea la AI extern în lansarea inițială.
- Revizuire umană a răspunsurilor reale pe corpusul de acceptare, fără date personale.
- Integrare selectivă într-o ramură proaspătă din main, nu merge automat al ramurii divergente.
- Teste de regresie, staging, rollback și acord explicit al utilizatorului înainte de lansare.

Acest document nu certifică lansarea AI extern și nu autorizează accesul la date școlare.
