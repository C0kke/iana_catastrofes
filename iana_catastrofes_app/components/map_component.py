import streamlit as st
import folium
from streamlit_folium import st_folium
from typing import Optional, Tuple, List, Dict, Any

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
        zoom_start=12 if (initial_lat and initial_lng) else 10,
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
    height: int = 400
):
    """Renderiza el mapa de monitoreo general sin interrumpir la navegación del usuario."""
    m = folium.Map(
        location=COQUIMBO_DEFAULT_CENTER,
        zoom_start=9,
        tiles="OpenStreetMap"
    )

    valid_markers = 0
    for p in projects:
        lat = p.get("latitude")
        lng = p.get("longitude")
        if lat is not None and lng is not None:
            try:
                lat_f = float(lat)
                lng_f = float(lng)
                
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
                    color = "yellow"
                    icon_type = "info-sign"
                else:
                    color = "green"
                    icon_type = "info-sign"
                
                name = p.get("name", "Emergencia")
                commune = p.get("commune", "")
                address = p.get("address", "")
                
                popup_html = f"""
                <div style="font-family: sans-serif; min-width: 190px;">
                    <b style="color: #0284c7;">{name}</b><br/>
                    <small><b>Estado:</b> {status.upper()}</small><br/>
                    <small><b>Comuna:</b> {commune}</small><br/>
                    <small><b>Dirección:</b> {address}</small><br/>
                    <small><b>Afectación:</b> {aff}</small><br/>
                    <small><b>Riesgo Personas:</b> {risk}</small><br/>
                    <small><b>Alerta:</b> <span style="font-weight: bold;">{alert_text}</span></small>
                </div>
                """
                
                folium.Marker(
                    location=[lat_f, lng_f],
                    popup=folium.Popup(popup_html, max_width=260),
                    tooltip=f"{name} ({aff} - {risk})",
                    icon=folium.Icon(color=color, icon=icon_type)
                ).add_to(m)
                
                valid_markers += 1
            except Exception as e:
                pass

    if valid_markers == 0:
        st.info("Aún no hay emergencias con coordenadas georreferenciadas. Puedes hacer clic al crear o editar una emergencia para ubicarla en el mapa.")
        
    st_folium(m, height=height, width=None, use_container_width=True, key="overview_emergencies_map")
