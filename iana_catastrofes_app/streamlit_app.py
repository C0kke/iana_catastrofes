import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)

if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import streamlit as st

try:
    from chatbot_emergencia_app.app.version import __version__
    from chatbot_emergencia_app.app.auth import render_login_screen, get_current_user
    from chatbot_emergencia_app.app.db import get_project_by_id
    from chatbot_emergencia_app.components.sidebar import render_sidebar
    from chatbot_emergencia_app.components.welcome import render_welcome_page
    from chatbot_emergencia_app.components.project_dashboard import render_project_dashboard
    from chatbot_emergencia_app.components.dialogs import render_new_project_dialog
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.version import __version__
        from iana_catastrofes_app.app.auth import render_login_screen, get_current_user
        from iana_catastrofes_app.app.db import get_project_by_id
        from iana_catastrofes_app.components.sidebar import render_sidebar
        from iana_catastrofes_app.components.welcome import render_welcome_page
        from iana_catastrofes_app.components.project_dashboard import render_project_dashboard
        from iana_catastrofes_app.components.dialogs import render_new_project_dialog
    except ModuleNotFoundError:
        from app.version import __version__
        from app.auth import render_login_screen, get_current_user
        from app.db import get_project_by_id
        from components.sidebar import render_sidebar
        from components.welcome import render_welcome_page
        from components.project_dashboard import render_project_dashboard
        from components.dialogs import render_new_project_dialog

INDEX_CSS_PATH = os.path.join(BASE_DIR, "index.css")

st.set_page_config(
    page_title=f"IANA - EMERGENCIA",
    layout="wide",
    initial_sidebar_state="expanded"
)

if os.path.exists(INDEX_CSS_PATH):
    with open(INDEX_CSS_PATH, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS = os.path.join(DATA_DIR, "uploads")
RESULTS = os.path.join(DATA_DIR, "results")

os.makedirs(UPLOADS, exist_ok=True)
os.makedirs(RESULTS, exist_ok=True)

st.session_state.setdefault("projects", [])
st.session_state.setdefault("active_project", None)
st.session_state.setdefault("active_tab", "Centro de Mando")
st.session_state.setdefault("show_new_project_dialog", False)
st.session_state.setdefault("show_edit_project_dialog", False)
st.session_state.setdefault("active_shift", "1")

param_proj_id = st.query_params.get("selected_proj_id")
if param_proj_id:
    proj_obj = get_project_by_id(param_proj_id)
    if proj_obj:
        st.session_state["active_project"] = proj_obj
        st.session_state["show_new_project_dialog"] = False
        st.session_state["show_edit_project_dialog"] = False
        if "selected_proj_id" in st.query_params:
            try:
                del st.query_params["selected_proj_id"]
            except Exception:
                pass
        st.rerun()

current_user = get_current_user()
if not current_user:
    render_login_screen()
    st.stop()

render_sidebar()

if st.session_state.get("show_new_project_dialog"):
    render_new_project_dialog()
    
active_proj = st.session_state.get("active_project")
if not active_proj:
    render_welcome_page()
else:
    render_project_dashboard()