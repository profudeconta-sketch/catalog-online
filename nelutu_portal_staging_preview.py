"""Experimental parent-portal-like Neluțu simulation.

This is a presentation shell for the EXISTING experimental Gemini preview,
not an imported copy of the real parent portal. It uses no school records.
"""
from __future__ import annotations
from pathlib import Path
import runpy
import sys
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.title("🤠 Neluțu-al-nost — simulare portal părinți")
st.info(
    "SIMULARE EXPERIMENTALĂ — fără autentificare de părinți, fără elevi reali "
    "și fără acces la catalogul școlar. Nu este portalul activ."
)
st.caption(
    "Aceeași logică experimentală Neluțu + tutorial + Gemini, "
    "cu protecțiile și comutatoarele existente. "
    "Dialogul generativ este disponibil doar operatorului autorizat."
)
st.markdown(
    "[Mergi la secțiunea dialog generativ experimental]"
    "(#nelutu-dialog-generativ-experimental)"
)
# Reuse the existing preview verbatim, including provider gates and budgets.
# Never fork the Gemini implementation or import school applications.
runpy.run_path(str(ROOT / "nelutu_gemini_preview.py"), run_name="__main__")

# Read-only lab diagnostics. Never expose DSN, table contents, or credentials.
st.divider()
st.subheader("🔒 Neon — verificare izolată, fără scrieri")
st.caption(
    "Verifică rolul și drepturile de execuție pentru contorul fictiv. "
    "Nu consumă cotă, nu modifică Neon și nu apelează Gemini."
)
if st.button("Verifică permisiunile Neon de laborator", key="nelutu_lab_runtime_check"):
    from nelutu_neon_runtime_permissions import runtime_permissions_ready
    _lab_dsn = st.secrets.get("NELUTU_TEST_DATABASE_URL", "")
    if not _lab_dsn:
        st.warning("Lipsește conexiunea izolată de laborator.")
    elif runtime_permissions_ready(_lab_dsn, enabled=True):
        st.success(
            "Rolul de laborator are drepturile necesare pentru contorul fictiv "
            "și nu are CREATE în schema de test sau acces la contorul Gemini."
        )
    else:
        st.warning(
            "Permisiunile de execuție nu sunt încă validate. "
            "Contorul de laborator rămâne blocat; nu se fac scrieri."
        )

st.caption("Verificare detaliată a tabelei de laborator — numai citire.")
if st.button("Verifică tabela și drepturile Neon", key="nelutu_lab_table_rights"):
    _dsn = st.secrets.get("NELUTU_TEST_DATABASE_URL", "")
    if not isinstance(_dsn, str) or not _dsn.startswith(("postgresql://", "postgres://")):
        st.warning("Conexiunea de laborator lipsește sau este invalidă.")
    else:
        try:
            import psycopg
            with psycopg.connect(_dsn, connect_timeout=5) as _conn:
                with _conn.cursor() as _cur:
                    _cur.execute(
                        "SELECT current_user = %s, "
                        "to_regclass('nelutu_test_concurenta.nelutu_streamlit_lab_budget') IS NOT NULL, "
                        "has_schema_privilege(current_user, 'nelutu_test_concurenta', 'USAGE'), "
                        "has_schema_privilege(current_user, 'nelutu_test_concurenta', 'CREATE')",
                        ("nelutu_test_runner",),
                    )
                    _role_ok, _table_exists, _usage, _create = _cur.fetchone()
                    if _table_exists:
                        _cur.execute(
                            "SELECT has_table_privilege(current_user, "
                            "'nelutu_test_concurenta.nelutu_streamlit_lab_budget', 'SELECT'), "
                            "has_table_privilege(current_user, "
                            "'nelutu_test_concurenta.nelutu_streamlit_lab_budget', 'UPDATE')"
                        )
                        _select, _update = _cur.fetchone()
                    else:
                        _select, _update = False, False
            st.write({
                "Rol de test corect": bool(_role_ok),
                "Tabela de laborator există": bool(_table_exists),
                "Drept USAGE": bool(_usage),
                "Drept SELECT": bool(_select),
                "Drept UPDATE": bool(_update),
                "Drept CREATE încă prezent": bool(_create),
            })
            st.caption("Verificare exclusiv SELECT; fără modificări sau apeluri Gemini.")
        except Exception:
            st.warning("Verificarea tabelei a eșuat; nu s-a efectuat nicio modificare.")

st.divider()
st.subheader("🧪 Contor fictiv persistent — laborator Neon")
st.caption(
    "Test exclusiv pe tabela izolată. Fără elevi, fără Gemini, "
    "fără resetare și fără scrieri automate."
)
from nelutu_streamlit_lab_budget import IsolatedLabBudget
_lab_counter_dsn = st.secrets.get("NELUTU_TEST_DATABASE_URL", "")
try:
    _lab_counter = IsolatedLabBudget(_lab_counter_dsn, enabled=True)
    if _lab_counter._ready():
        st.metric("Unități fictive rămase (maximum 3)", _lab_counter.remaining())
        if st.button("Consumă 1 unitate fictivă de test", key="nelutu_lab_reserve_one"):
            if _lab_counter.reserve():
                st.success("O unitate fictivă a fost rezervată în Neon. Reîncarcă pagina pentru verificare.")
            else:
                st.warning("Rezervare refuzată sau limită atinsă; nicio unitate suplimentară acordată.")
    else:
        st.warning("Contorul rămâne blocat: drepturile runtime nu sunt validate.")
except (TypeError, ValueError):
    st.warning("Conexiunea izolată lipsește sau este invalidă.")

st.divider()
st.subheader("⚡ Test rapid: două sesiuni, un singur contor")
st.caption(
    "Un singur clic lansează două rezervări concurente pe contorul fictiv. "
    "Nu resetează limita, nu folosește Gemini și nu accesează date școlare. "
    "Cu 2 unități rămase, cel mult 2 rezervări pot reuși."
)
if st.button("Execută testul simultan (2 cereri)", key="nelutu_lab_parallel_two"):
    from concurrent.futures import ThreadPoolExecutor
    from nelutu_streamlit_lab_budget import IsolatedLabBudget
    _parallel_dsn = st.secrets.get("NELUTU_TEST_DATABASE_URL", "")
    try:
        _parallel_budget = IsolatedLabBudget(_parallel_dsn, enabled=True)
        if not _parallel_budget._ready():
            st.warning("Test blocat: permisiunile de execuție nu sunt validate.")
        else:
            _before = _parallel_budget.remaining()
            with ThreadPoolExecutor(max_workers=2) as _pool:
                _results = list(_pool.map(lambda _: _parallel_budget.reserve(), range(2)))
            _after = _parallel_budget.remaining()
            st.write({
                "Unități înainte": _before,
                "Rezervări acceptate": sum(_results),
                "Rezervări refuzate": 2 - sum(_results),
                "Unități după": _after,
            })
            if _before - _after == sum(_results) and _after >= 0:
                st.success("Test simultan coerent: fără depășirea limitei.")
            else:
                st.error("Test neconcludent: valorile necesită investigație.")
    except (TypeError, ValueError):
        st.warning("Conexiunea izolată lipsește sau este invalidă.")

st.divider()
st.subheader("🛑 Verificare finală: limită epuizată")
st.caption("O singură încercare fictivă; nu resetează contorul și nu apelează Gemini.")
if st.button("Verifică refuzul după epuizare", key="nelutu_lab_exhaustion"):
    from nelutu_streamlit_lab_budget import IsolatedLabBudget
    _exhaust_dsn = st.secrets.get("NELUTU_TEST_DATABASE_URL", "")
    try:
        _exhaust_budget = IsolatedLabBudget(_exhaust_dsn, enabled=True)
        if not _exhaust_budget._ready():
            st.warning("Verificarea este blocată: permisiuni runtime nevalidate.")
        else:
            _exhaust_before = _exhaust_budget.remaining()
            if _exhaust_before != 0:
                st.warning("Contorul nu este epuizat; testul de refuz nu a fost executat.")
            else:
                _accepted = _exhaust_budget.reserve()
                _exhaust_after = _exhaust_budget.remaining()
                st.write({
                    "Unități înainte": _exhaust_before,
                    "Cerere suplimentară acceptată": _accepted,
                    "Unități după": _exhaust_after,
                })
                if not _accepted and _exhaust_after == 0:
                    st.success("PASS: cererea suplimentară a fost refuzată; limita rămâne zero.")
                else:
                    st.error("FAIL: comportament neașteptat; opriți testele.")
    except (TypeError, ValueError):
        st.warning("Conexiunea izolată lipsește sau este invalidă.")
