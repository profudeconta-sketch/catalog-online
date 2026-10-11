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

st.caption("Diagnostic suplimentar: verificare separată a rolului și schemei, fără scrieri.")
if st.button("Diagnostic Neon: rol și schemă", key="nelutu_lab_setup_diagnostic"):
    from nelutu_neon_isolated_diagnostic import diagnose_isolated_neon
    _lab_dsn_diag = st.secrets.get("NELUTU_TEST_DATABASE_URL", "")
    _lab_status = diagnose_isolated_neon(_lab_dsn_diag)
    st.info("Rezultat diagnostic: " + _lab_status)
    if _lab_status == "ready":
        st.warning(
            "Diagnosticul inițial confirmă dreptul CREATE. "
            "Pentru execuția contorului, acest drept trebuie eliminat "
            "după pregătirea tabelei, de către administratorul Neon."
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
