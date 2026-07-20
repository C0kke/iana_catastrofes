import streamlit as st
from datetime import datetime

try:
    from chatbot_emergencia_app.app.db import get_chile_now_iso, list_projects
    from chatbot_emergencia_app.components.map_component import render_emergencies_overview_map
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.db import get_chile_now_iso, list_projects
        from iana_catastrofes_app.components.map_component import render_emergencies_overview_map
    except ModuleNotFoundError:
        from app.db import get_chile_now_iso, list_projects
        from components.map_component import render_emergencies_overview_map

def render_welcome_page():
    chile_iso = get_chile_now_iso()
    try:
        dt_chile = datetime.fromisoformat(chile_iso)
        time_str = dt_chile.strftime("%d/%m/%Y - %H:%M:%S (Hora Chile)")
    except Exception:
        time_str = chile_iso

    current_shift = st.session_state.get("active_shift", "1")

    st.markdown("""
        <div style="background-color: var(--card-bg); border-radius: 12px; padding: 2rem; border: 1px solid var(--card-border); margin-bottom: 1.5rem;">
            <h1 style="color: var(--blue-title); margin-top: 0; font-size: 2.2rem; font-weight: 800;">Chatbot Emergencia - Centro de Mando Municipal</h1>
            <p style="color: var(--text-primary); font-size: 1.05rem; line-height: 1.5; margin-bottom: 0;">
                Herramienta de análisis, criterios y toma de decisiones para la coordinación de cuadrillas y respuesta rápida en la <strong>Región de Coquimbo</strong> ante anegamientos, temporales y aislamiento municipal.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        new_shift = st.text_input("TURNO ACTIVO", value=current_shift, help="Ingresa el número o identificador del turno de trabajo")
        if new_shift != current_shift:
            st.session_state["active_shift"] = new_shift

    with col_t2:
        st.markdown(f"""
            <div style="background-color: var(--card-bg); border: 1px solid var(--blue-title); padding: 10px 16px; border-radius: 8px; text-align: right; margin-top: 6px;">
                <div style="color: var(--blue-title); font-weight: bold; font-size: 0.85rem; text-transform: uppercase;">HORA DE CHILE</div>
                <div style="color: var(--text-primary); font-size: 1.1rem; font-weight: 700; margin-top: 2px;">{time_str}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    tab_mapa, tab_historial = st.tabs(["Mapa de Monitoreo Georreferenciado", "Historial de Emergencias Tratadas / Solucionadas"])

    with tab_mapa:
        st.markdown("### Mapa General de Emergencias - Región de Coquimbo")
        st.caption("Usa el mapa libremente para desplazar, hacer zoom y revisar la distribución geográfica de los eventos.")
        all_projects = list_projects()
        render_emergencies_overview_map(all_projects, height=450)

    with tab_historial:
        st.markdown("### Historial de Emergencias Resueltas / Tratadas")
        resolved_list = list_projects(status_filter="solucionada") + list_projects(status_filter="tratada")
        if not resolved_list:
            st.info("Aún no hay emergencias marcadas como tratadas o solucionadas en el sistema.")
        else:
            for r in resolved_list:
                with st.expander(f"✓ {r.get('name', 'Emergencia')} - Comuna: {r.get('commune', 'N/A')} ({r.get('chile_time', '')})"):
                    st.write(f"**Dirección:** {r.get('address', '')}")
                    st.write(f"**Sector:** {r.get('sector', '')}")
                    st.write(f"**Turno:** {r.get('shift_number', '1')}")
                    st.write(f"**Nivel Afectación Real:** {r.get('real_affectation_level', r.get('affectation_level', ''))}")
                    st.write(f"**Riesgo Real Personas:** {r.get('real_people_risk', r.get('people_risk', ''))}")
                    st.write(f"**Resumen Operativo:** {r.get('consolidated_context', '')}")
                    if st.button("Ver Detalle Completo", key=f"hist_btn_{r.get('id')}"):
                        st.session_state["active_project"] = r
                        st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Tarjetas de pasos
    st.markdown("""
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem;">
            <div style="background: var(--card-bg); padding: 1.2rem; border-radius: 8px; border: 1px solid var(--card-border);">
                <h3 style="color: var(--blue-title); margin-top: 0;">1. Registrar Emergencia Comunal</h3>
                <p style="color: var(--text-secondary); font-size: 0.95rem;">Ingresa la comuna (La Serena, Coquimbo, Ovalle, Vicuña, etc.), dirección, sector, coordenadas y requerimientos.</p>
            </div>
            <div style="background: var(--card-bg); padding: 1.2rem; border-radius: 8px; border: 1px solid var(--card-border);">
                <h3 style="color: var(--blue-title); margin-top: 0;">2. Análisis Multimodal de Evidencia</h3>
                <p style="color: var(--text-secondary); font-size: 0.95rem;">Sube fotografías de terreno, informes Word de inspectores o minutas en PDF para procesar el estado real del evento.</p>
            </div>
            <div style="background: var(--card-bg); padding: 1.2rem; border-radius: 8px; border: 1px solid var(--card-border);">
                <h3 style="color: var(--blue-title); margin-top: 0;">3. Criterios & Despacho de Cuadrillas</h3>
                <p style="color: var(--text-secondary); font-size: 0.95rem;">Evalúa el Nivel de Afectación y Riesgo a Personas para derivar a CGE (Luz) o Aguas del Valle (Agua/Colectores).</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.info("Selecciona una emergencia en el panel lateral o presiona 'Registrar Nueva Emergencia' para iniciar.")