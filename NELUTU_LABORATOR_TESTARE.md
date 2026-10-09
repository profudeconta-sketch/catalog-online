# Laborator Neluțu — verificare locală, fără publicare

**Statut:** experimental; numai ramura `nelutu-local-dialogue-launch-20261009`. Nu modificați `main`, Streamlit Cloud, Secrets sau datele catalogului.

## Condiții de siguranță
- Testați într-un mediu local separat, pe date fictive, fără fișierele private Excel/JSON și fără tokenuri.
- Nu introduceți nume de elevi, CNP-uri, parole, documente sau informații reale.
- Laboratorul este dezactivat implicit și nu înlocuiește Neluțu din Portalul Părinților.
- Modulul folosește răspunsuri locale prestabilite, **nu AI generativ**. Nu promite identificarea tuturor situațiilor de risc.
- Nu publicați laboratorul pe internet și nu configurați acces extern.

## Pornire locală (Windows PowerShell)
Dintr-o copie separată a ramurii experimentale:

```powershell
python -m pip install "streamlit>=1.35,<2"
$env:NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL = "1"
python -m streamlit run nelutu_dialogue_preview.py --server.address localhost
```

Deschideți numai adresa locală afișată de Streamlit. Pentru oprire, apăsați Ctrl+C și eliminați variabila:

```powershell
Remove-Item Env:NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL
```

## Probe manuale
1. „De ce învățăm la școală?” — răspuns educațional.
2. „Dă-mi un exemplu” — continuare a aceleiași teme.
3. „Cum trimit scutirea medicală?” — răspunsul existent despre portal are prioritate și tema educațională se șterge.
4. „Șterge contextul conversației” — răspunsul și tema dispar.
5. Deschideți o sesiune separată — nu trebuie să preia tema sesiunii precedente.
6. Folosiți **doar text fictiv** pentru o întrebare sensibilă — mesaj de îndrumare, fără a cere identitatea copilului.

## Criterii de oprire
Opriți testarea și nu integrați dacă apare o excepție, se pierde izolarea sesiunilor, se afișează date personale, se accesează un registru școlar sau se produce un răspuns care poate induce în eroare într-o situație de risc.

## Limitări
GitHub Actions verifică logica și widgeturile cu Streamlit AppTest; aceasta **nu este** echivalentă cu o verificare vizuală în browser, pe mobil, ori cu un audit de securitate complet. Integrarea în portal necesită evaluare separată și aprobarea explicită finală.
