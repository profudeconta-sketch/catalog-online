# Neluțu-AI — registru de verificare experimentală

Acest document privește numai prototipul din ramura experimentală. **Nu certifică pregătirea pentru producție.**

## Defecte identificate și intervenții

| Problemă | Intervenție | Stadiu |
| --- | --- | --- |
| Greșeli de română în examenele LIVE #3–#5 | Instrucțiuni lingvistice îmbunătățite și corecții locale conservatoare, inclusiv „repetai la intervale crescute” | Implementat; corectorul nu este exhaustiv |
| Răspunsuri uneori prea formale și adresare inconsistentă | Instrucțiuni explicite pentru naturalețe, acorduri, adresare și regionalisme autentice | Implementat; necesită evaluare umană pe răspunsuri noi |
| Răspuns Cloudflare mai lung de limita locală, tăiat fără avertizare | Respingere cu `oversized_response`, în loc de afișarea unei propoziții trunchiate | Implementat; test de regresie adăugat |
| `ResourceWarning: unclosed file` în testul asistentului | Deschidere cu `with open(...)` | Implementat; de confirmat în jurnalul următor |
| Teste noi care puteau lipsi din lista explicită | Descoperire automată `test_nelutu_*.py` | Implementat |

## Protecții care trebuie păstrate

- AI extern numai pentru întrebări educaționale publice exact aprobate; fără istoric și fără date școlare.
- Fără modificări ale `app_parinti.py`, `app_web_catalog.py`, fișierelor Excel/JSON ori documentelor școlare în cadrul acestui experiment.
- Fără activare implicită, fără îmbinare în `main` a prototipului înainte de evaluare și aprobare.
- Examenul LIVE este manual și transmite exclusiv cele trei întrebări publice din lista fixă.

## Blocaje înainte de activare în Streamlit

1. **Calitatea limbii:** un set mai mare de răspunsuri reale, verificat manual; corecțiile prin regex nu pot garanta gramatica.
2. **Dialog real:** întrebările externe sunt fără istoric; nu există conversație multi-turn generativă verificată. Continuitatea trebuie proiectată fără scurgeri de date.
3. **Securitate și autorizare:** analiză a integrării cu sesiunea autentificată și separarea elevilor/părinților.
4. **Costuri:** limita gratuită și protecția împotriva facturării trebuie verificate în contul furnizorului, nu deduse dintr-o limită pe sesiune.
5. **Validare completă:** execuția testelor pe ultimul commit, verificare interfață mobil/desktop și plan de revenire înainte de implementare.

Ultima versiune pregătită pentru validare offline: `b95e2fb6ffe3c91a622054e212c4310939236d6c`. Nu se consemnează un rezultat verde până la existența jurnalului de execuție.
