import json
import os
import streamlit as st
from datetime import datetime

try:
    from chatbot_emergencia_app.app.db import create_project, update_project_details, get_chile_now_iso, create_critical_point, update_critical_point, list_critical_points, delete_critical_point
    from chatbot_emergencia_app.components.map_component import render_location_picker_map
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.db import create_project, update_project_details, get_chile_now_iso, create_critical_point, update_critical_point, list_critical_points, delete_critical_point
        from iana_catastrofes_app.components.map_component import render_location_picker_map
    except ModuleNotFoundError:
        from app.db import create_project, update_project_details, get_chile_now_iso, create_critical_point, update_critical_point, list_critical_points, delete_critical_point
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
    "Infraestructura Privada",
    "Emergencia riesgo social"
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

def _close_new_project_dialog():
    st.session_state["show_new_project_dialog"] = False

@st.dialog("Registrar Nueva Emergencia", width="large", on_dismiss=_close_new_project_dialog)
def render_new_project_dialog():
    st.markdown('<div class="iana-modal-wrapper"></div>', unsafe_allow_html=True)
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
        selected_commune = st.selectbox("Comuna", options=COMMUNES_COQUIMBO, index=0)

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

    missing_fields = []
    if not name or not name.strip():
        missing_fields.append("Nombre / Código de la Emergencia")
    if not sector or not sector.strip():
        missing_fields.append("Sector")
    if not selected_emergency_types:
        missing_fields.append("Tipo de Emergencia (selecciona al menos uno)")

    can_submit = len(missing_fields) == 0

    st.markdown("---")
    if missing_fields:
        st.warning(f"Campos obligatorios faltantes: **{', '.join(missing_fields)}**")

    if st.button("Guardar e Inicializar Emergencia", type="primary", width="stretch", disabled=not can_submit):
        try:
            # project_type usa 'other' como valor seguro; los tipos detallados están en emergency_types (JSONB)
            main_type = "other"
            
            new_p = create_project(
                name=name.strip(),
                shift_number=shift_number,
                chile_time=chile_now_str,
                address=sector.strip(),
                sector=sector.strip(),
                project_category=project_category,
                project_type=main_type,
                emergency_types=selected_emergency_types,
                description=description.strip(),
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

            saved_id = new_p.get("id", "")
            if not saved_id or str(saved_id).startswith("local-"):
                st.error("Error al guardar emergencia. Intenta nuevamente.")
                return

            st.success(f"¡Emergencia '{name}' registrada exitosamente! (ID: {saved_id})")
            st.session_state["show_new_project_dialog"] = False
            st.session_state["active_project"] = new_p
            st.session_state.pop("dlg_lat", None)
            st.session_state.pop("dlg_lng", None)
            import time
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Error al registrar la emergencia: {e}")

def _close_edit_project_dialog():
    st.session_state["show_edit_project_dialog"] = False

@st.dialog("Editar Datos de la Emergencia", width="large", on_dismiss=_close_edit_project_dialog)
def render_edit_project_dialog(project: dict):
    st.markdown('<div class="iana-modal-wrapper"></div>', unsafe_allow_html=True)
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
    if st.button("Guardar Cambios de la Emergencia", type="primary", width="stretch"):
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

SEVERITY_LABELS = {
    "CRÍTICO": "CRÍTICO",
    "ALTO": "ALTO",
    "MEDIO": "MEDIO",
    "BAJO": "BAJO"
}

TYPE_LABELS = {
    "ruta_cortada": "Ruta Cortada",
    "socavon": "Socavón",
    "derrumbe": "Derrumbe",
    "aluvion": "Aluvión",
    "caida_puente": "Caída de Puente",
    "aislamiento": "Aislamiento",
    "otro": "Otro"
}

def _close_critical_point_dialog():
    st.session_state["show_new_critical_point_dialog"] = False

@st.dialog("Puntos Críticos / Rutas Cortadas", width="large", on_dismiss=_close_critical_point_dialog)
def render_new_critical_point_dialog():
    """Modal con tabs para crear y gestionar Puntos Críticos."""
    st.markdown('<div class="iana-modal-wrapper"></div>', unsafe_allow_html=True)

    tab_crear, tab_gestionar = st.tabs(["Crear Nuevo", "Gestionar Existentes"])

    # ─── TAB 1: CREAR NUEVO PUNTO CRÍTICO ───
    with tab_crear:
        st.caption("Ingresa la ubicación, gravedad y tipo de interrupción vial o peligro inminente.")

        name = st.text_input("NOMBRE / IDENTIFICADOR *", placeholder="Ej: Ruta D-43 Km 15 - Socavón Masivo", key="cp_create_name")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            selected_commune = st.selectbox("COMUNA *", options=COMMUNES_COQUIMBO, index=0, key="cp_commune_sel")
        with col_c2:
            sector = st.text_input("SECTOR / SEÑALIZACIÓN *", placeholder="Ej: Pan de Azúcar / Cruce Ruta 43", key="cp_create_sector")

        address = st.text_input("DIRECCIÓN / REFERENCIA", placeholder="Ej: Av. Costanera con Peñuelas", key="cp_create_address")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            point_type = st.selectbox(
                "TIPO DE AFECTACIÓN VIAL / CRÍTICA *",
                options=["ruta_cortada", "socavon", "derrumbe", "aluvion", "caida_puente", "aislamiento", "otro"],
                format_func=lambda x: TYPE_LABELS.get(x, x),
                index=0,
                key="cp_create_type"
            )
        with col_t2:
            severity = st.selectbox(
                "SEVERIDAD *",
                options=["CRÍTICO", "ALTO", "MEDIO", "BAJO"],
                index=0,
                key="cp_create_severity"
            )

        description = st.text_area("DESCRIPCIÓN *", placeholder="Detalla si el tránsito está 100% cortado, riesgos para personas y maquinaria requerida.", key="cp_create_desc")

        st.markdown("#### Georreferenciación en Terreno (Opcional)")
        cur_lat = st.session_state.get("cp_new_lat")
        cur_lng = st.session_state.get("cp_new_lng")

        pick_lat, pick_lng = render_location_picker_map(initial_lat=cur_lat, initial_lng=cur_lng, key_prefix="cp_new_picker")
        if pick_lat != cur_lat or pick_lng != cur_lng:
            st.session_state["cp_new_lat"] = pick_lat
            st.session_state["cp_new_lng"] = pick_lng
            cur_lat, cur_lng = pick_lat, pick_lng

        if cur_lat and cur_lng:
            st.success(f"Coordenadas fijadas: {cur_lat}, {cur_lng}")

        # Validación
        missing = []
        if not name or not name.strip():
            missing.append("Nombre")
        if not sector or not sector.strip():
            missing.append("Sector")
        if not description or not description.strip():
            missing.append("Descripción")

        can_save = len(missing) == 0

        st.markdown("---")
        if missing:
            st.warning(f"Campos obligatorios faltantes: **{', '.join(missing)}**")

        if st.button("Guardar Punto Crítico", type="primary", width="stretch", key="save_cp_btn", disabled=not can_save):
            try:
                cp = create_critical_point(
                    name=name.strip(),
                    commune=selected_commune,
                    sector=sector.strip(),
                    address=address,
                    point_type=point_type,
                    severity=severity,
                    latitude=cur_lat,
                    longitude=cur_lng,
                    description=description.strip(),
                    status="activo"
                )
                st.success("Punto Crítico registrado e ingresado al mapa.")
                st.session_state["show_new_critical_point_dialog"] = False
                st.session_state.pop("cp_new_lat", None)
                st.session_state.pop("cp_new_lng", None)
                import time
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar punto crítico: {e}")

    with tab_gestionar:
        all_cps = list_critical_points()

        if not all_cps:
            st.info("No hay puntos críticos registrados actualmente.")
        else:
            st.caption(f"{len(all_cps)} punto(s) crítico(s) registrado(s)")

            for cp in all_cps:
                cp_id = cp.get("id", "")
                cp_name = cp.get("name", "Sin Nombre")
                cp_severity = cp.get("severity", "MEDIO")
                cp_type = cp.get("point_type", "otro")
                cp_status = cp.get("status", "activo")
                cp_commune = cp.get("commune", "")
                cp_sector = cp.get("sector", "")

                severity_label = SEVERITY_LABELS.get(cp_severity, cp_severity)
                type_label = TYPE_LABELS.get(cp_type, cp_type)

                severity_color = "#dc2626" if cp_severity == "CRÍTICO" else ("#d97706" if cp_severity == "ALTO" else ("#ca8a04" if cp_severity == "MEDIO" else "#16a34a"))
                status_color = "#16a34a" if cp_status == "resuelto" else ("#d97706" if cp_status == "en_mitigacion" else "#dc2626")
                status_text = "Resuelto" if cp_status == "resuelto" else ("En Mitigación" if cp_status == "en_mitigacion" else "Activo")

                st.markdown(f"""
                <style>
                    div[data-testid="stVerticalBlock"]:has(> div > div > button[key="del_cp_{cp_id}"]) {{
                        background: var(--card-bg);
                        border: 1px solid var(--card-border);
                        border-radius: 8px;
                        padding: 0.7rem 1rem;
                        margin-bottom: 0.5rem;
                    }}
                </style>
                """, unsafe_allow_html=True)
                with st.container(border=True):
                    col_info, col_status, col_btn = st.columns([3, 1, 1])
                    with col_info:
                        st.markdown(f"""
                        <span style="font-weight: 700; color: var(--blue-title);">{cp_name}</span><br/>
                        <small style="color: var(--text-secondary);">
                            <span style="color: {severity_color}; font-weight: 600;">{severity_label}</span> · {type_label} · {cp_commune} - {cp_sector}
                        </small>
                        """, unsafe_allow_html=True)
                    with col_status:
                        st.markdown(f"""
                        <span style="background: {status_color}; color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; white-space: nowrap;">{status_text}</span>
                        """, unsafe_allow_html=True)
                    with col_btn:
                        if st.button("Eliminar", key=f"del_cp_{cp_id}", type="secondary"):
                            try:
                                delete_critical_point(cp_id)
                                st.success(f"Punto '{cp_name}' eliminado.")
                                import time
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al eliminar: {e}")

def render_edit_critical_point_dialog(cp: dict):
    """Modal para editar o cambiar estado de un Punto Crítico existente."""
    cp_id = cp.get("id")
    st.markdown(f"### Editar Punto Crítico: {cp.get('name', 'Punto Crítico')}")

    if st.button("Cerrar Edición", key="close_edit_cp_btn"):
        st.session_state["active_edit_cp"] = None
        st.rerun()

    name = st.text_input("NOMBRE *", value=cp.get("name", ""))
    sector = st.text_input("SECTOR *", value=cp.get("sector", ""))
    address = st.text_input("DIRECCIÓN / REFERENCIA", value=cp.get("address", ""))
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        cur_type = cp.get("point_type", "ruta_cortada")
        type_opts = ["ruta_cortada", "socavon", "derrumbe", "aluvion", "caida_puente", "aislamiento", "otro"]
        t_idx = type_opts.index(cur_type) if cur_type in type_opts else 0
        point_type = st.selectbox("TIPO DE AFECTACIÓN", options=type_opts, index=t_idx)

    with col_t2:
        cur_status = cp.get("status", "activo")
        st_opts = ["activo", "en_mitigacion", "resuelto"]
        s_idx = st_opts.index(cur_status) if cur_status in st_opts else 0
        status = st.selectbox("ESTADO", options=st_opts, index=s_idx)

    description = st.text_area("DESCRIPCIÓN", value=cp.get("description", ""))

    st.markdown("---")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("Guardar Cambios del Punto Crítico", type="primary", width="stretch"):
            try:
                update_critical_point(
                    point_id=cp_id,
                    name=name,
                    sector=sector,
                    address=address,
                    point_type=point_type,
                    status=status,
                    description=description
                )
                st.success("¡Punto crítico actualizado!")
                st.session_state["active_edit_cp"] = None
                st.rerun()
            except Exception as e:
                st.error(f"Error al actualizar: {e}")