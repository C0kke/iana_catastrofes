import streamlit as st

try:
    from chatbot_emergencia_app.app.db import list_projects
    from chatbot_emergencia_app.app.auth import get_current_user, is_read_only, logout_user
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.db import list_projects
        from iana_catastrofes_app.app.auth import get_current_user, is_read_only, logout_user
    except ModuleNotFoundError:
        from app.db import list_projects
        from app.auth import get_current_user, is_read_only, logout_user

def render_sidebar():
    user = get_current_user()
    read_only = is_read_only()

    with st.sidebar:
        st.markdown("<h2 style='color: var(--blue-title); font-weight: 800; margin-bottom: 0;'>IANA - EMERGENCIA</h2>", unsafe_allow_html=True)

        st.caption("Sistema de Registro y Gestión en Tiempo Real")
        st.divider()

        if user:
            st.markdown(f"""
                <div style="background-color: var(--card-bg); padding: 0.8rem; border-radius: 8px; border: 1px solid var(--card-border); margin-bottom: 1rem;">
                    <div style="font-weight: bold; color: var(--blue-title); font-size: 0.95rem;">{user.get('name')}</div>
                    <small style="color: var(--text-secondary);">{user.get('title')}</small><br/>
                </div>
            """, unsafe_allow_html=True)

            if st.button("Cerrar Sesión", use_container_width=True, key="btn_logout"):
                logout_user()

            st.divider()

        if st.button("Inicio / Mapa General", use_container_width=True, key="btn_go_home"):
            st.session_state["active_project"] = None
            st.session_state["show_new_project_dialog"] = False
            st.session_state["show_edit_project_dialog"] = False
            st.rerun()

        if not read_only:
            if st.button("+ Registrar Nueva Emergencia", use_container_width=True, type="primary", key="btn_new_project_trigger"):
                st.session_state["show_new_project_dialog"] = True
                st.markdown("---")

        st.markdown("### Emergencias Activas")
        
        all_projects = list_projects()
        st.session_state["projects"] = all_projects
        
        active_projects = [p for p in all_projects if p.get("status", "activa") == "activa"]
        resolved_projects = [p for p in all_projects if p.get("status", "activa") in ["tratada", "solucionada"]]

        active_proj_obj = st.session_state.get("active_project") or {}
        active_proj_id = active_proj_obj.get("id")

        if not active_projects:
            st.info("No hay emergencias activas.")
        else:
            for proj in active_projects:
                proj_name = proj.get("name", "Sin Nombre")
                proj_id = proj.get("id")
                
                is_active = (active_proj_id == proj_id)
                btn_label = f"• {proj_name}" if not is_active else f"[Activa] {proj_name}"
                
                if st.button(btn_label, key=f"proj_btn_{proj_id}", use_container_width=True):
                    st.session_state["active_project"] = proj
                    st.session_state["show_new_project_dialog"] = False
                    st.session_state["show_edit_project_dialog"] = False
                    st.session_state["active_tab"] = "Centro de Mando"
                    st.rerun()