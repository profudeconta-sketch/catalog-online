# Neluțu conversațional — prototip Cloudflare AI

**Stare:** modul experimental separat, neconectat la aplicația părinților; nu se execută cereri externe în producție.

## Condiții pentru activare ulterioară

1. Cont Cloudflare cu Workers AI și verificarea cotei gratuite curente.
2. Token cu permisiuni minime, stocat numai în Streamlit Secrets, niciodată în GitHub.
3. Acord explicit privind transmiterea întrebărilor generale către furnizorul extern; nu se trimit nume, date ale elevilor sau documente.
4. Verificarea disponibilității și calității modelului `@cf/qwen/qwen3-30b-a3b-fp8`; modelul este configurabil.
5. Teste de integrare, limitare a cererilor, tratarea erorilor și mesaj de fallback fără cost.
6. Testare separată a conversațiilor în limba română și a informațiilor legislative; modelul nu este sursă oficială actualizată.

## Limitări

Filtrul local de confidențialitate este **conservator, dar nu poate garanta** identificarea tuturor datelor personale. Nu activați transmiterea liberă a întrebărilor fără măsuri suplimentare (consimțământ, minimizare, validare și evaluare de protecție a datelor). Nu există garanție de utilizare nelimitată gratuită.

## Teste

`python -m unittest -v test_nelutu_cloudflare_ai.py`

Testele simulează răspunsul Cloudflare fără rețea și verifică absența configurării implicite.
