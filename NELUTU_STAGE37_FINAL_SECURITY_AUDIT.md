# Neluțu — Etapa 37: audit final al experimentului

Data: 2026-10-10. Domeniu: numai ramura feature/nelutu-gemini-safe-foundation (PR #112).

## Dovezi verificate
- Commit e73cbdc574944ae0dcf0d100a22ee2fbff252fa3: ambele workflow-uri GitHub Actions au concluzia success: Nelutu offline regression tests; Notification center tests.
- Comparația main...feature indică numai 19 fișiere ale experimentului, ale testelor și ale rapoartelor. Niciun fișier din aplicația profesorilor, aplicația părinților sau datele catalogului nu este modificat.
- Apelurile cu mesaje individuale au allowlist exact pentru cele nouă prompturi demonstrative, iar dialogurile fixe au allowlist separat.
- Limitele UI sunt 3 încercări per sesiune și 12 per proces, cu rezervare sincronizată în același proces; fără retry automat.

## Riscuri reziduale / blocaje de producție
1. Contoarele sunt volatile la restart și nu sunt comune mai multor instanțe. Nu reprezintă o cotă provider-wide sau un plafon de cost.
2. Nu există confirmare independentă a cotelor, restricțiilor de cheie și stării de facturare din consola Google.
3. Filtrarea de date personale este euristică; doar lista exactă de mesaje fictive permite siguranța experimentului curent, nu dialog liber.
4. Nu a fost efectuată evaluarea de confidențialitate pentru date școlare și nici un test end-to-end autorizat în producție.
5. Testele GitHub sunt offline și nu certifică disponibilitatea serviciului Gemini în timp real.

## Verdict
GO: păstrarea demonstrației izolate, exclusiv cu mesaje fictive aprobate și testele offline.
NO-GO: integrarea cu catalogul școlar, activarea dialogului liber, acces la date școlare, merge în main sau facturare.

Orice schimbare a verdictului necesită cerere și aprobare explicită, plus rezolvarea verificabilă a blocajelor. Regula de Aur rămâne obligatorie.
