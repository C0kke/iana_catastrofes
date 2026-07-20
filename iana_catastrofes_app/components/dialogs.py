import json
import os
import streamlit as st
from datetime import datetime

try:
    from chatbot_emergencia_app.app.db import create_project, update_project_details, get_chile_now_iso
    from chatbot_emergencia_app.components.map_component import render_location_picker_map
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.db import create_project, update_project_details, get_chile_now_iso
        from iana_catastrofes_app.components.map_component import render_location_picker_map
    except ModuleNotFoundError:
        from app.db import create_project, update_project_details, get_chile_now_iso
        from components.map_component import render_location_picker_map

COMMUNES_COQUIMBO = [
    "Coquimbo",
    "La Serena",
    "Ovalle",

    "Vicuña",
    "Illapel",
    "Los Vilos",
    "Andacollo",
    "Combarbalá",
    "Monte Patria",
    "Punitaqui",
    "Río Hurtado",
    "Salamanca",
    "Canela",
    "La Higuera",
    "Paihuano"
]

PROJECT_CATEGORY_OPTIONS = [
    "Grandes Ítems",
    "Caminos y Carreteras",
    "Infraestructura Pública",
    "Puentes",
    "Infraestructura Privada"
]

TIPOS_EMERGENCIA_OPCIONES = [
    "Inundacion",
    "Anegamiento",
    "Remocion en masa",
    "Derrumbe",
    "Socavón",
    "Caida de Arbol",
    "Caida de Poste",
    "Daño ESTRUCTURAL",
    "Rotura de Matriz",
    "Daño en pavimento",
    "Daño en vereda",
    "Daño en Plaza",
    "Daño en Alumbrado",
    "Emergencia Costera"
]

AFECTACION_OPCIONES = [
    "Vivienda",
    "Personas",
    "Vehiculos",
    "Infraestructura Municipal",
    "Infraestructura Publica",
    "Áreas Verdes",
    "Equipamiento",
    "Red Electrica",
    "Agua Potable",
    "Alcantarillado",
    "Transito",
    "Ninguna"
]

REQUERIMIENTO_OPCIONES = [
    "Retroexcavadora",
    "Camión Tolva",
    "Camion Aljibe",
    "Camión Pluma",
    "Cuadrilla Municipal",
    "Electrico",
    "Constructor",
    "Ingeniero",
    "Arquitecto",
    "Topografia",
    "Señalizacion"
]

@st.dialog("Registrar Nueva Emergencia")
def render_new_project_dialog():
    st.write("Completa la información oficial para registrar el evento de emergencia en tiempo real.")

    chile_now_str = get_chile_now_iso()
    try:
        dt_chile = datetime.fromisoformat(chile_now_str)
        chile_time_display = dt_chile.strftime("%d/%m/%Y %H:%M:%S (Hora Chile)")
    except Exception:
        chile_time_display = chile_now_str

    default_shift = st.session_state.get("active_shift", "1")

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        shift_number = st.text_input("NÚMERO DE TURNO *", value=default_shift, placeholder="Ej: Turno 1 / Mañana")
    with col_t2:
        st.text_input("HORA DE REGISTRO (Automático en Hora Chile)", value=chile_time_display, disabled=True)

    name = st.text_input("NOMBRE / CÓDIGO DE LA EMERGENCIA *", placeholder="Ej: Anegamiento Sector Balmaceda / Socavón Ruta 41 Vicuña")

    col_cat, col_sec = st.columns(2)
    with col_cat:
        project_category = st.selectbox(
            "TIPO DE PROYECTO *",
            options=PROJECT_CATEGORY_OPTIONS,
            index=1,
            help="Selecciona la categoría o ítem de la infraestructura afectada"
        )
    with col_sec:
        sector = st.text_input("SECTOR *", placeholder="Ej: Sector Las Compañías, San Juan, Parte Alta")

    col_reg, col_com = st.columns(2)
    with col_reg:
        selected_region = st.selectbox("Región", options=["Coquimbo"], index=0, disabled=True)
    with col_com:
        selected_commune = st.selectbox("Comuna", options=COMMUNES_COQUIMBO, index=1)

    # Georeferenciación interactiva en mapa
    st.markdown("#### GEORREFERENCIACIÓN Y UBICACIÓN EN MAPA")
    st.caption("Selecciona la ubicación exacta en el mapa de la Región de Coquimbo.")
    
    cur_lat = st.session_state.get("dlg_lat")
    cur_lng = st.session_state.get("dlg_lng")

    picked_lat, picked_lng = render_location_picker_map(cur_lat, cur_lng, key_prefix="dialog_creation")
    if (picked_lat != cur_lat or picked_lng != cur_lng) and picked_lat is not None and picked_lng is not None:
        st.session_state["dlg_lat"] = picked_lat
        st.session_state["dlg_lng"] = picked_lng
        st.session_state["show_new_project_dialog"] = True
        st.rerun()

    col_lat, col_lng = st.columns(2)
    with col_lat:
        lat_val_str = st.text_input("LATITUD", value=str(st.session_state.get("dlg_lat", "")), placeholder="Ej: -29.9533")
    with col_lng:
        lng_val_str = st.text_input("LONGITUD", value=str(st.session_state.get("dlg_lng", "")), placeholder="Ej: -71.3395")

    try:
        final_lat = float(lat_val_str) if lat_val_str else None
        final_lng = float(lng_val_str) if lng_val_str else None
    except ValueError:
        final_lat, final_lng = None, None

    st.markdown("#### TIPO DE EMERGENCIA *")
    selected_emergency_types = []
    cols_type = st.columns(2)
    for idx, opt in enumerate(TIPOS_EMERGENCIA_OPCIONES):
        with cols_type[idx % 2]:
            if st.checkbox(opt, key=f"type_chk_{idx}"):
                selected_emergency_types.append(opt)

    otro_tipo_check = st.checkbox("Otro Tipo de Emergencia", key="type_chk_other")
    if otro_tipo_check:
        otro_tipo_val = st.text_input("Especifica otro tipo de emergencia", key="type_other_val")
        if otro_tipo_val:
            selected_emergency_types.append(f"Otro: {otro_tipo_val}")

    description = st.text_area("DESCRIPCIÓN *", placeholder="Describe la situación en terreno...")

    col_af, col_ri = st.columns(2)
    with col_af:
        affectation_level = st.radio("NIVEL DE AFECTACIÓN", options=["Baja", "Media", "Alta", "Crítica"], index=1)
    with col_ri:
        people_risk = st.radio("RIESGO PARA LAS PERSONAS", options=["Sin riesgo", "Riesgo Bajo", "Riesgo Medio", "Riesgo Alto", "Riesgo Inminente"], index=2)

    st.markdown("#### AFECTACIÓN *")
    selected_affectations = []
    cols_afec = st.columns(2)
    for idx, opt in enumerate(AFECTACION_OPCIONES):
        with cols_afec[idx % 2]:
            if st.checkbox(opt, key=f"afec_chk_{idx}"):
                selected_affectations.append(opt)

    st.markdown("#### REQUERIMIENTO *")
    selected_requirements = []
    cols_req = st.columns(2)
    for idx, opt in enumerate(REQUERIMIENTO_OPCIONES):
        with cols_req[idx % 2]:
            if st.checkbox(opt, key=f"req_chk_{idx}"):
                selected_requirements.append(opt)

    otro_req_check = st.checkbox("Otro Requerimiento", key="req_chk_other")
    if otro_req_check:
        otro_req_val = st.text_input("Especifica otro requerimiento", key="req_other_val")
        if otro_req_val:
            selected_requirements.append(f"Otro: {otro_req_val}")

    attention_priority = st.radio("PRIORIDAD DE ATENCIÓN", options=["INMEDIATA", "DENTRO DEL DIA", "24 HRS", "PROGRAMADA"], index=1)

    observations = st.text_area("OBSERVACIONES", placeholder="Observaciones adicionales...")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        follow_up_str = st.radio("SEGUIMIENTO", options=["NO", "SI"], index=0)
        follow_up_bool = (follow_up_str == "SI")
    with col_f2:
        follow_up_responsible = st.text_input("RESPONSABLE DE SEGUIMIENTO", placeholder="Nombre o unidad responsable")

    st.markdown("---")
    if st.button("Guardar e Inicializar Emergencia", type="primary", use_container_width=True):
        if not name or not sector:
            st.error("El nombre y el sector son obligatorios.")
        else:
            try:
                main_type = selected_emergency_types[0].lower().replace(" ", "_") if selected_emergency_types else "other"
                
                new_p = create_project(
                    name=name,
                    shift_number=shift_number,
                    chile_time=chile_now_str,
                    address=sector,
                    sector=sector,
                    project_category=project_category,
                    project_type=main_type,
                    emergency_types=selected_emergency_types,
                    description=description,
                    affectation_level=affectation_level,
                    people_risk=people_risk,
                    affectations=selected_affectations,
                    requirements_list=selected_requirements,
                    attention_priority=attention_priority,
                    observations=observations,
                    follow_up=follow_up_bool,
                    follow_up_responsible=follow_up_responsible,
                    region=selected_region,
                    commune=selected_commune,
                    latitude=final_lat,
                    longitude=final_lng,
                    status="activa"
                )
                st.success("¡Emergencia registrada exitosamente!")
                st.session_state["show_new_project_dialog"] = False
                st.session_state["active_project"] = new_p
                st.session_state.pop("dlg_lat", None)
                st.session_state.pop("dlg_lng", None)
                st.rerun()
            except Exception as e:
                st.error(f"Error al registrar la emergencia: {e}")

@st.dialog("Editar Datos de la Emergencia")
def render_edit_project_dialog(project: dict):
    st.write("Modifica o actualiza la información técnica de la emergencia.")

    proj_id = project.get("id")
    name = st.text_input("NOMBRE / CÓDIGO DE LA EMERGENCIA *", value=project.get("name", ""))

    cur_category = project.get("project_category", "Caminos y Carreteras")
    cat_idx = PROJECT_CATEGORY_OPTIONS.index(cur_category) if cur_category in PROJECT_CATEGORY_OPTIONS else 0
    project_category = st.selectbox("TIPO DE PROYECTO *", options=PROJECT_CATEGORY_OPTIONS, index=cat_idx)

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        shift_number = st.text_input("NÚMERO DE TURNO *", value=project.get("shift_number", "1"))
    with col_t2:
        st.text_input("HORA DE REGISTRO", value=project.get("chile_time", ""), disabled=True)

    sector = st.text_input("SECTOR *", value=project.get("sector", ""))

    col_reg, col_com = st.columns(2)
    with col_reg:
        selected_region = st.selectbox("Región", options=["Coquimbo"], index=0, disabled=True)

    cur_commune = project.get("commune", "Coquimbo")
    com_idx = COMMUNES_COQUIMBO.index(cur_commune) if cur_commune in COMMUNES_COQUIMBO else 0
    with col_com:
        selected_commune = st.selectbox("Comuna", options=COMMUNES_COQUIMBO, index=com_idx)

    st.markdown("#### GEORREFERENCIACIÓN Y UBICACIÓN EN MAPA")
    cur_lat = st.session_state.get("edit_lat", project.get("latitude"))
    cur_lng = st.session_state.get("edit_lng", project.get("longitude"))

    picked_lat, picked_lng = render_location_picker_map(cur_lat, cur_lng, key_prefix=f"edit_dialog_{proj_id}")
    if (picked_lat != cur_lat or picked_lng != cur_lng) and picked_lat is not None and picked_lng is not None:
        st.session_state["edit_lat"] = picked_lat
        st.session_state["edit_lng"] = picked_lng
        st.session_state["show_edit_project_dialog"] = True
        st.rerun()

    col_lat, col_lng = st.columns(2)
    with col_lat:
        lat_val_str = st.text_input("LATITUD", value=str(st.session_state.get("edit_lat", project.get("latitude") or "")), placeholder="Ej: -29.9533")
    with col_lng:
        lng_val_str = st.text_input("LONGITUD", value=str(st.session_state.get("edit_lng", project.get("longitude") or "")), placeholder="Ej: -71.3395")

    try:
        final_lat = float(lat_val_str) if lat_val_str else None
        final_lng = float(lng_val_str) if lng_val_str else None
    except ValueError:
        final_lat, final_lng = None, None

    description = st.text_area("DESCRIPCIÓN *", value=project.get("description", ""))

    cur_af = project.get("affectation_level", "Media")
    af_opts = ["Baja", "Media", "Alta", "Crítica"]
    af_idx = af_opts.index(cur_af) if cur_af in af_opts else 1

    cur_ri = project.get("people_risk", "Riesgo Medio")
    ri_opts = ["Sin riesgo", "Riesgo Bajo", "Riesgo Medio", "Riesgo Alto", "Riesgo Inminente"]
    ri_idx = ri_opts.index(cur_ri) if cur_ri in ri_opts else 2

    col_af, col_ri = st.columns(2)
    with col_af:
        affectation_level = st.radio("NIVEL DE AFECTACIÓN DECLARADO", options=af_opts, index=af_idx)
    with col_ri:
        people_risk = st.radio("RIESGO PARA LAS PERSONAS DECLARADO", options=ri_opts, index=ri_idx)

    cur_priority = project.get("attention_priority", "DENTRO DEL DIA")
    prio_opts = ["INMEDIATA", "DENTRO DEL DIA", "24 HRS", "PROGRAMADA"]
    prio_idx = prio_opts.index(cur_priority) if cur_priority in prio_opts else 1
    attention_priority = st.radio("PRIORIDAD DE ATENCIÓN", options=prio_opts, index=prio_idx)

    observations = st.text_area("OBSERVACIONES", value=project.get("observations", ""))

    st.markdown("---")
    if st.button("Guardar Cambios de la Emergencia", type="primary", use_container_width=True):
        if not name or not sector:
            st.error("El nombre y el sector son obligatorios.")
        else:
            try:
                updated_proj = update_project_details(
                    project_id=proj_id,
                    name=name,
                    shift_number=shift_number,
                    address=sector,
                    sector=sector,
                    project_category=project_category,
                    emergency_types=project.get("emergency_types", []),
                    description=description,
                    affectation_level=affectation_level,
                    people_risk=people_risk,
                    affectations=project.get("affectations", []),
                    requirements_list=project.get("requirements_list", []),
                    attention_priority=attention_priority,
                    observations=observations,
                    follow_up=project.get("follow_up", False),
                    follow_up_responsible=project.get("follow_up_responsible", ""),
                    region=selected_region,
                    commune=selected_commune,
                    latitude=final_lat,
                    longitude=final_lng
                )
                st.success("¡Datos de la emergencia actualizados exitosamente!")
                st.session_state["show_edit_project_dialog"] = False
                st.session_state["active_project"] = updated_proj if updated_proj else project
                st.session_state.pop("edit_lat", None)
                st.session_state.pop("edit_lng", None)
                st.rerun()
            except Exception as e:
                st.error(f"Error al actualizar la emergencia: {e}")