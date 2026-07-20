import streamlit as st
from datetime import datetime

try:
    from chatbot_emergencia_app.app.db import get_chile_now_iso, list_projects
    from chatbot_emergencia_app.app.auth import get_current_user, is_read_only
    from chatbot_emergencia_app.components.map_component import render_emergencies_overview_map
    from chatbot_emergencia_app.components.commune_dashboard import render_commune_impact_dashboard
    from chatbot_emergencia_app.components.weather_dashboard import render_weather_monitoring_tab
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.db import get_chile_now_iso, list_projects
        from iana_catastrofes_app.app.auth import get_current_user, is_read_only
        from iana_catastrofes_app.components.map_component import render_emergencies_overview_map
        from iana_catastrofes_app.components.commune_dashboard import render_commune_impact_dashboard
        from iana_catastrofes_app.components.weather_dashboard import render_weather_monitoring_tab
    except ModuleNotFoundError:
        from app.db import get_chile_now_iso, list_projects
        from app.auth import get_current_user, is_read_only
        from components.map_component import render_emergencies_overview_map
        from components.commune_dashboard import render_commune_impact_dashboard
        from components.weather_dashboard import render_weather_monitoring_tab

def render_welcome_page():
    user = get_current_user()
    read_only = is_read_only()

    chile_iso = get_chile_now_iso()
    try:
        dt_chile = datetime.fromisoformat(chile_iso)
        time_str = dt_chile.strftime("%d/%m/%Y - %H:%M:%S (Hora Chile)")
    except Exception:
        time_str = chile_iso

    current_shift = st.session_state.get("active_shift", "1")

    st.markdown("""
        <div style="background-color: var(--card-bg); border-radius: 12px; padding: 1.8rem; border: 1px solid var(--card-border); margin-bottom: 1.2rem;">
            <h1 style="color: var(--blue-title); margin-top: 0; font-size: 2.2rem; font-weight: 800;">IANA - EMERGENCIA</h1>
            <p style="color: var(--text-primary); font-size: 1.05rem; line-height: 1.5; margin-bottom: 0;">
                Herramienta de análisis, criterios y toma de decisiones para la coordinación de cuadrillas y respuesta rápida en la <strong>Región de Coquimbo</strong> ante anegamientos, temporales y aislamiento municipal.
            </p>
        </div>
    """, unsafe_allow_html=True)


    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        new_shift = st.text_input("TURNO ACTIVO", value=current_shift, help="Ingresa el número o identificador del turno de trabajo", disabled=read_only)
        if new_shift != current_shift and not read_only:
            st.session_state["active_shift"] = new_shift

    with col_t2:
        st.markdown(f"""
            <div style="background-color: var(--card-bg); border: 1px solid var(--blue-title); padding: 10px 16px; border-radius: 8px; text-align: right; margin-top: 6px;">
                <div style="color: var(--blue-title); font-weight: bold; font-size: 0.85rem; text-transform: uppercase;">HORA OFICIAL CHILE</div>
                <div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 700; margin-top: 2px;">{time_str}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    all_projects = list_projects()
    active_list = [p for p in all_projects if p.get("status", "activa") == "activa"]
    resolved_list = [p for p in all_projects if p.get("status", "activa") in ["tratada", "solucionada"]]
    critical_list = [p for p in active_list if p.get("real_affectation_level") in ["Crítica", "Critica"] or p.get("real_people_risk") == "Riesgo Inminente"]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric(label="TOTAL CATASTRO REGIONAL", value=len(all_projects))
    with m2:
        st.metric(label="EMERGENCIAS ACTIVAS", value=len(active_list))
    with m3:
        st.metric(label="CRÍTICAS / RIESGO INMINENTE", value=len(critical_list))
    with m4:
        st.metric(label="TRATADAS / RESUELTAS", value=len(resolved_list))

    st.markdown("<br/>", unsafe_allow_html=True)

    if read_only:
        tab_mapa, tab_clima, tab_historial, tab_dashboard = st.tabs([
            "Mapa de Monitoreo Georreferenciado",
            "Monitoreo Climático Regional",
            "Historial de Emergencias Tratadas / Solucionadas",
            "Dashboard de Impacto Comunal (Jefatura)"
        ])
    else:
        tab_mapa, tab_clima, tab_historial = st.tabs([
            "Mapa de Monitoreo Georreferenciado",
            "Monitoreo Climático Regional",
            "Historial de Emergencias Tratadas / Solucionadas"
        ])
        tab_dashboard = None

    with tab_mapa:
        st.markdown("### Mapa General de Emergencias - Región de Coquimbo")
        st.caption("Usa el mapa libremente para desplazar, hacer zoom y revisar la distribución geográfica de los eventos.")
        render_emergencies_overview_map(all_projects, height=480)

    with tab_clima:
        render_weather_monitoring_tab()
        
    with tab_historial:
        st.markdown("### Historial de Emergencias Resueltas / Tratadas")
        if not resolved_list:
            st.info("Aún no hay emergencias marcadas como tratadas o solucionadas en el sistema.")
        else:
            for r in resolved_list:
                with st.expander(f"[Resuelta] {r.get('name', 'Emergencia')} - Comuna: {r.get('commune', 'N/A')} ({r.get('chile_time', '')})"):
                    st.write(f"**Categoría:** `{r.get('project_category', 'Infraestructura')}`")
                    st.write(f"**Dirección:** {r.get('address', '')}")
                    st.write(f"**Sector:** {r.get('sector', '')}")
                    st.write(f"**Turno:** {r.get('shift_number', '1')}")
                    st.write(f"**Nivel Afectación Real:** {r.get('real_affectation_level', r.get('affectation_level', ''))}")
                    st.write(f"**Riesgo Real Personas:** {r.get('real_people_risk', r.get('people_risk', ''))}")
                    st.write(f"**Resumen Operativo:** {r.get('consolidated_context', '')}")
                    if st.button("Ver Detalle Completo", key=f"hist_btn_{r.get('id')}"):
                        st.session_state["active_project"] = r
                        st.rerun()

    if tab_dashboard:
        with tab_dashboard:
            render_commune_impact_dashboard(all_projects)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.info("Selecciona una emergencia en el panel lateral para revisar su información detallada.")