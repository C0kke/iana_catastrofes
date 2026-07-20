import streamlit as st

try:
    from chatbot_emergencia_app.app.db import list_projects
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.db import list_projects
    except ModuleNotFoundError:
        from app.db import list_projects

def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='color: var(--blue-title); font-weight: 800; margin-bottom: 0;'>CHATBOT EMERGENCIA</h2>", unsafe_allow_html=True)
        st.caption("Sistema Abierto de Registro y Gestión de Emergencias")
        st.divider()

        if st.button("+ Registrar Nueva Emergencia", use_container_width=True, type="primary"):
            st.session_state["show_new_project_dialog"] = True

        st.markdown("---")
        
        # Botón para volver al Inicio / Mapa General
        if st.button("🏠 Inicio / Mapa General", use_container_width=True):
            st.session_state["active_project"] = None
            st.rerun()

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
                    st.session_state["active_tab"] = "Centro de Mando"
                    st.rerun()

        st.markdown("---")
        st.markdown("### Historial de Emergencias Resueltas")
        if not resolved_projects:
            st.caption("No hay emergencias en el historial resuelto.")
        else:
            for proj in resolved_projects:
                proj_name = proj.get("name", "Sin Nombre")
                proj_id = proj.get("id")
                
                is_active = (active_proj_id == proj_id)
                btn_label = f"✓ {proj_name}" if not is_active else f"[Ver] {proj_name}"
                
                if st.button(btn_label, key=f"proj_btn_res_{proj_id}", use_container_width=True):
                    st.session_state["active_project"] = proj
                    st.session_state["active_tab"] = "Centro de Mando"
                    st.rerun()