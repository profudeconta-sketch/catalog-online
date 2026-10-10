# Neluțu — Etapa 35: limite persistente și controlul furnizorului

Domeniu: experiment izolat. Nu există autorizare pentru integrarea în catalog.

## Ce poate fi verificat din cod
- Maximum 3 încercări Gemini per sesiune și 12 per proces Streamlit, prin SharedBudgetGate sincronizat.
- Mesajele trimise prin generate/diagnose_status sunt limitate la prompturile publice prestabilite.
- Cele patru transcrieri fixe sunt aprobate prin comparație exactă înaintea transportului.
- Nu există reîncercări automate în fluxurile de demonstrație.

## Ce NU este garantat
- Contorul procesului nu persistă după repornire și nu este comun mai multor replici/servere.
- Funcțiile de transport pot fi apelate de alte componente Python care dețin cheia; limitele UI nu sunt un control global la nivel furnizor.
- Nu am acces verificat la configurația Google AI Studio/Google Cloud pentru cheia respectivă; nu afirm că există o limită de cheltuieli sau o restricție de cheie configurată.
- O limită persistentă multi-instanta ar necesita un registru atomic comun, mecanism de expirare și izolare de datele școlare; NU se va improviza folosind fișierele Excel/JSON ale catalogului.
- Nu este dovedită o evaluare juridică/organizațională pentru transferul datelor școlare către Gemini.

## Condiții de activare în producție
1. Cheie separată pentru experiment, fără billing activat fără aprobare.
2. Cote și restricții verificate în consola furnizorului, inclusiv comportamentul la epuizare.
3. Dacă se permite vreodată trafic real din aplicația școlară: gateway server-side independent de UI, cu limitare persistentă, autentificare, control de acces, audit fără conținut sensibil și mecanism de oprire.
4. Evaluare de confidențialitate și aprobare explicită pentru orice nou flux de date.
5. Testare de regresie și verificare manuală pe scenarii fictive, înainte de orice merge.

Decizie: prototipul poate continua doar în regim controlat; integrarea în aplicațiile școlare rămâne NO-GO.
