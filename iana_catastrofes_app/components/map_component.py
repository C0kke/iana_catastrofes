import streamlit as st
import folium
from streamlit_folium import st_folium
from typing import Optional, Tuple, List, Dict, Any

try:
    from chatbot_emergencia_app.app.auth import get_current_user
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.auth import get_current_user
    except ModuleNotFoundError:
        from app.auth import get_current_user

COQUIMBO_DEFAULT_CENTER = (-29.9533, -71.3395)

def render_location_picker_map(
    initial_lat: Optional[float] = None,
    initial_lng: Optional[float] = None,
    key_prefix: str = "picker"
) -> Tuple[Optional[float], Optional[float]]:
    """Mapa interactivo para seleccionar latitud y longitud al hacer clic en terreno."""
    lat_val = initial_lat if initial_lat is not None else COQUIMBO_DEFAULT_CENTER[0]
    lng_val = initial_lng if initial_lng is not None else COQUIMBO_DEFAULT_CENTER[1]
    
    m = folium.Map(
        location=[lat_val, lng_val],
        zoom_start=18 if (initial_lat and initial_lng) else 12,
        tiles="OpenStreetMap"
    )

    if initial_lat is not None and initial_lng is not None:
        folium.Marker(
            location=[initial_lat, initial_lng],
            popup="Ubicación Seleccionada",
            tooltip="Punto Registrado",
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    st.caption("Haz clic en cualquier punto del mapa para seleccionar o ajustar las coordenadas de terreno.")
    
    map_data = st_folium(
        m,
        height=300,
        width=None,
        use_container_width=True,
        key=f"{key_prefix}_folium_map"
    )

    if map_data and map_data.get("last_clicked"):
        clicked_lat = round(map_data["last_clicked"]["lat"], 6)
        clicked_lng = round(map_data["last_clicked"]["lng"], 6)
        if clicked_lat != initial_lat or clicked_lng != initial_lng:
            return clicked_lat, clicked_lng

    return initial_lat, initial_lng

def render_emergencies_overview_map(
    projects: List[Dict[str, Any]],
    critical_points: List[Dict[str, Any]] = [],
    height: int = 440
):
    """Renderiza el mapa de monitoreo general con emergencias y marcadores 'X' de Puntos Críticos / Rutas Cortadas."""
    
    if not st.session_state.get("show_new_project_dialog"):
        st.session_state["show_new_project_dialog"] = False
    if not st.session_state.get("show_new_critical_point_dialog"):
        st.session_state["show_new_critical_point_dialog"] = False
    if not st.session_state.get("show_edit_project_dialog"):
        st.session_state["show_edit_project_dialog"] = False

    m = folium.Map(
        location=COQUIMBO_DEFAULT_CENTER,
        zoom_start=9,
        tiles="OpenStreetMap"
    )

    valid_markers = 0
    
    for p in projects:
        lat = p.get("latitude")
        lng = p.get("longitude")
        p_id = p.get("id")
        if lat is not None and lng is not None and p_id:
            try:
                lat_f = float(lat)
                lng_f = float(lng)
                
                category = p.get("project_category", "Infraestructura")
                aff = p.get("real_affectation_level", p.get("affectation_level", "Media"))
                risk = p.get("real_people_risk", p.get("people_risk", "Riesgo Medio"))
                status = p.get("status", "activa")
                alert_text = p.get("overall_alert_level", f"{aff} - {risk}")
                
                if status in ["tratada", "solucionada"]:
                    color = "blue"
                    icon_type = "ok-sign"
                elif aff in ["Crítica", "Critica"] or risk == "Riesgo Inminente":
                    color = "red"
                    icon_type = "warning-sign"
                elif aff == "Alta" or risk == "Riesgo Alto":
                    color = "orange"
                    icon_type = "exclamation-sign"
                elif aff == "Media" or risk == "Riesgo Medio":
                    color = "beige"
                    icon_type = "info-sign"
                else:
                    color = "green"
                    icon_type = "info-sign"
                
                name = p.get("name", "Emergencia")
                commune = p.get("commune", "")
                sector = p.get("sector", "")
                
                popup_html = f"""
                <div style="font-family: system-ui, -apple-system, sans-serif; min-width: 220px; padding: 4px;">
                    <b style="color: #0284c7; font-size: 1.05rem;">{name}</b><br/>
                    <small><b>Ítem:</b> {category}</small><br/>
                    <small><b>Estado:</b> {status.upper()}</small><br/>
                    <small><b>Comuna:</b> {commune}</small><br/>
                    <small><b>Sector:</b> {sector}</small><br/>
                    <small><b>Afectación Real:</b> {aff}</small><br/>
                    <small><b>Riesgo Personas:</b> {risk}</small><br/>
                    <small><b>Alerta Global:</b> <span style="font-weight: bold; color: #0284c7;">{alert_text}</span></small>
                </div>
                """
                
                folium.Marker(
                    location=[lat_f, lng_f],
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=f"{name} ({aff} - {risk})",
                    icon=folium.Icon(color=color, icon=icon_type)
                ).add_to(m)
                
                valid_markers += 1
            except Exception as e:
                pass

    for cp in critical_points:
        cp_lat = cp.get("latitude")
        cp_lng = cp.get("longitude")
        if cp_lat is not None and cp_lng is not None:
            try:
                cp_lat_f = float(cp_lat)
                cp_lng_f = float(cp_lng)
                cp_name = cp.get("name", "Punto Crítico")
                cp_type = cp.get("point_type", "ruta_cortada")
                cp_sev = cp.get("severity", "CRÍTICO")
                cp_desc = cp.get("description", "")
                cp_commune = cp.get("commune", "")
                cp_sector = cp.get("sector", "")
                cp_status = cp.get("status", "activo")

                is_campamento = (cp_type == "campamento")
                header_title = "CAMPAMENTO REGISTRADO" if is_campamento else "RUTA CORTADA / PUNTO CRÍTICO"
                header_color = "#7c3aed" if is_campamento else "#dc2626"
                type_display = "Campamento" if is_campamento else cp_type

                if cp_status == "resuelto":
                    marker_color = "gray"
                elif is_campamento:
                    marker_color = "purple"
                else:
                    marker_color = "darkred"

                marker_icon = "home" if is_campamento else "remove"

                cp_popup = f"""
                <div style="font-family: system-ui, -apple-system, sans-serif; min-width: 210px; padding: 4px;">
                    <b style="color: {header_color}; font-size: 1.05rem;">{header_title}</b><br/>
                    <b>{cp_name}</b><br/>
                    <small><b>Tipo:</b> {type_display}</small><br/>
                    <small><b>Severidad:</b> <span style="color: {header_color}; font-weight: bold;">{cp_sev}</span></small><br/>
                    <small><b>Ubicación:</b> {cp_commune} ({cp_sector})</small><br/>
                    <small><b>Estado:</b> {cp_status.upper()}</small><br/>
                    <p style="margin-top: 6px; font-size: 0.82rem; color: #475569;">{cp_desc}</p>
                </div>
                """

                tooltip_text = f"CAMPAMENTO: {cp_name} ({cp_commune})" if is_campamento else f"RUTA CORTADA: {cp_name} ({cp_commune})"

                folium.Marker(
                    location=[cp_lat_f, cp_lng_f],
                    popup=folium.Popup(cp_popup, max_width=290),
                    tooltip=tooltip_text,
                    icon=folium.Icon(color=marker_color, icon=marker_icon, prefix="glyphicon")
                ).add_to(m)
                
                valid_markers += 1
            except Exception as e:
                pass

    if valid_markers == 0:
        st.info("Aún no hay emergencias ni puntos críticos georreferenciados en el mapa.")

    map_data = st_folium(m, height=height, width=None, use_container_width=True, key="overview_emergencies_map")

    if map_data and map_data.get("last_object_clicked"):
        click_obj = map_data["last_object_clicked"]
        c_lat = click_obj.get("lat")
        c_lng = click_obj.get("lng")
        if c_lat is not None and c_lng is not None:
            matched_proj = next(
                (p for p in projects if p.get("latitude") and p.get("longitude") 
                 and abs(float(p["latitude"]) - c_lat) < 0.0008 
                 and abs(float(p["longitude"]) - c_lng) < 0.0008),
                None
            )
            if matched_proj:
                st.session_state["selected_map_project"] = matched_proj

    selected_proj = st.session_state.get("selected_map_project")
    if selected_proj:
        proj_name = selected_proj.get("name", "Emergencia")
        proj_commune = selected_proj.get("commune", "")
        
        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
        col_info, col_btn = st.columns([3, 1])
        with col_info:
            st.markdown(f"**Emergencia Seleccionada en Mapa:** <span style='color: var(--blue-title); font-weight: 700;'>{proj_name}</span> ({proj_commune})", unsafe_allow_html=True)
        with col_btn:
            if st.button("Ir a vista de Evento", type="primary", key="btn_nav_selected_map_event", width="stretch"):
                st.session_state["active_project"] = selected_proj
                st.session_state["active_tab"] = "Centro de Mando"
                st.session_state["show_new_project_dialog"] = False
                st.session_state["show_edit_project_dialog"] = False
                st.session_state["show_new_critical_point_dialog"] = False
                st.session_state.pop("selected_map_project", None)
                st.rerun()