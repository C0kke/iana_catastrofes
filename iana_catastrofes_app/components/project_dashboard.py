import os
import streamlit as st
import tempfile
from datetime import datetime

try:
    from chatbot_emergencia_app.app.pdf_extract import extract_text_from_file
    from chatbot_emergencia_app.app.rules_engine import evaluate_emergency_rules
    from chatbot_emergencia_app.app.ai_verifier import analyze_single_document, consolidate_accident_evaluation, dump_obj
    from chatbot_emergencia_app.app.db import (
        get_project_by_id,
        update_project_evaluation,
        update_project_coordinates,
        update_project_status,
        add_document_to_project,
        add_document_analysis,
        list_project_documents
    )
    from chatbot_emergencia_app.app.auth import is_read_only
    from chatbot_emergencia_app.components.map_component import render_location_picker_map
    from chatbot_emergencia_app.components.dialogs import render_edit_project_dialog
    from chatbot_emergencia_app.components.weather_dashboard import render_compact_weather_widget
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.pdf_extract import extract_text_from_file
        from iana_catastrofes_app.app.rules_engine import evaluate_emergency_rules
        from iana_catastrofes_app.app.ai_verifier import analyze_single_document, consolidate_accident_evaluation, dump_obj
        from iana_catastrofes_app.app.db import (
            get_project_by_id,
            update_project_evaluation,
            update_project_coordinates,
            update_project_status,
            add_document_to_project,
            add_document_analysis,
            list_project_documents
        )
        from iana_catastrofes_app.app.auth import is_read_only
        from iana_catastrofes_app.components.map_component import render_location_picker_map
        from iana_catastrofes_app.components.dialogs import render_edit_project_dialog
        from iana_catastrofes_app.components.weather_dashboard import render_compact_weather_widget
    except ModuleNotFoundError:
        from app.pdf_extract import extract_text_from_file
        from app.rules_engine import evaluate_emergency_rules
        from app.ai_verifier import analyze_single_document, consolidate_accident_evaluation, dump_obj
        from app.db import (
            get_project_by_id,
            update_project_evaluation,
            update_project_coordinates,
            update_project_status,
            add_document_to_project,
            add_document_analysis,
            list_project_documents
        )
        from app.auth import is_read_only
        from components.map_component import render_location_picker_map
        from components.dialogs import render_edit_project_dialog
        from components.weather_dashboard import render_compact_weather_widget

DOC_TYPES_MAP = {
    "site_photo": "Evidencia Fotográfica / Terreno",
    "word_report": "Informe Word / Ficha de Campo (.docx)",
    "police_report": "Parte Policial / SIAT Carabineros",
    "medical_triage_log": "Ficha de Triage SAMU / Atención Médica",
    "witness_statement": "Declaración de Testigo / Involucrado",
    "hazmat_sheet": "Hoja de Seguridad Química (HDT HazMat)",
    "other": "Otro Documento de Campo"
}

def render_project_dashboard():
    read_only = is_read_only()

    project = st.session_state.get("active_project")
    if not project:
        st.warning("No hay ninguna emergencia seleccionada.")
        return

    proj_id = project.get("id")
    fresh_proj = get_project_by_id(proj_id)
    if fresh_proj:
        project = fresh_proj
        st.session_state["active_project"] = fresh_proj

    proj_name = project.get("name", "Emergencia")
    shift_number = project.get("shift_number", "1")
    chile_time_raw = project.get("chile_time", "")
    address = project.get("address", "")
    sector = project.get("sector", "")
    project_category = project.get("project_category", "Infraestructura Pública")
    emergency_types = project.get("emergency_types", [])
    description = project.get("description", "")
    initial_affectation = project.get("affectation_level", "Media")
    initial_risk = project.get("people_risk", "Riesgo Medio")
    affectations = project.get("affectations", [])
    requirements_list = project.get("requirements_list", [])
    attention_priority = project.get("attention_priority", "DENTRO DEL DIA")
    observations = project.get("observations", "")
    follow_up = project.get("follow_up", False)
    follow_up_resp = project.get("follow_up_responsible", "")
    status = project.get("status", "activa")

    region = project.get("region", "Coquimbo")
    commune = project.get("commune", "Coquimbo")
    lat_val = project.get("latitude")
    lng_val = project.get("longitude")

    context = project.get("consolidated_context", "Sin datos acumulados.")
    real_affectation = project.get("real_affectation_level", initial_affectation)
    real_risk = project.get("real_people_risk", initial_risk)
    alert_level = project.get("overall_alert_level", f"{real_affectation.upper()} - {real_risk.upper()}")
    risk_eval = project.get("initial_vs_real_risk_evaluation", "")
    mitigations = project.get("mitigation_actions", [])
    recommendations = project.get("action_recommendations", [])
    entities = project.get("recommended_entities", [])
    infractions = project.get("consolidated_infractions", [])
    metadata = project.get("extracted_metadata", [])

    try:
        dt_c = datetime.fromisoformat(chile_time_raw)
        chile_time_fmt = dt_c.strftime("%d/%m/%Y %H:%M:%S (Chile)")
    except Exception:
        chile_time_fmt = chile_time_raw

    # Renderizar modal de edición si está activo
    if st.session_state.get("show_edit_project_dialog", False):
        render_edit_project_dialog(project)

    # Header de la Emergencia con botones de acción persistentes
    col_h1, col_h2, col_h3, col_h4 = st.columns([2.2, 1.4, 1.0, 1.0])
    with col_h1:
        status_badge = "[TRATADA / SOLUCIONADA]" if status in ["tratada", "solucionada"] else "[EMERGENCIA ACTIVA]"
        badge_bg = "#16a34a" if status in ["tratada", "solucionada"] else "#0284c7"
        st.markdown(f"""
            <div style="background-color: var(--card-bg); border-radius: 10px; padding: 1rem 1.2rem; border: 1px solid var(--card-border); margin-bottom: 0.8rem;">
                <span style="background-color: {badge_bg}; color: #ffffff; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">
                    {status_badge}
                </span>
                <span style="background-color: #0284c7; color: #ffffff; padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; font-weight: bold; margin-left: 8px;">
                    ÍTEM: {project_category.upper()}
                </span>
                <h2 style="color: var(--blue-title); margin: 6px 0 0 0; font-size: 1.6rem; font-weight: 800;">{proj_name}</h2>
                <p style="color: var(--text-primary); margin-top: 4px; font-size: 0.9rem;">
                    Ubicación: <strong>{address}</strong> ({sector}), Comuna de <strong>{commune}</strong>, {region} | Turno #{shift_number}
                </p>
            </div>
        """, unsafe_allow_html=True)

    render_compact_weather_widget(commune)

    with col_h2:
        if st.button("Ejecutar / Reevaluar Análisis con IA", type="primary", use_container_width=True, help="Ejecuta o reevalúa inmediatamente la emergencia con la Inteligencia Artificial"):
            with st.spinner("Ejecutando evaluación..."):
                try:
                    docs = list_project_documents(proj_id)
                    latest_summary = f"Tipo de Proyecto: {project_category}. " + (description if description else "Emergencia registrada en terreno.")
                    if docs:
                        latest_summary += f" Se cuenta con {len(docs)} evidencia(s) registradas."

                    eval_res = consolidate_accident_evaluation(
                        previous_context=context,
                        new_doc_summary=latest_summary,
                        new_doc_infractions=[],
                        new_doc_metadata=[],
                        initial_affectation_level=initial_affectation,
                        initial_people_risk=initial_risk,
                        previous_infractions=infractions,
                        previous_metadata=metadata
                    )

                    update_project_evaluation(
                        project_id=proj_id,
                        consolidated_context=eval_res.consolidated_context,
                        initial_vs_real_risk_evaluation=eval_res.initial_vs_real_risk_evaluation,
                        real_affectation_level=eval_res.real_affectation_level,
                        real_people_risk=eval_res.real_people_risk,
                        overall_alert_level=eval_res.overall_alert_level,
                        mitigation_actions=eval_res.mitigation_actions,
                        action_recommendations=eval_res.action_recommendations,
                        recommended_entities=[dump_obj(e) for e in eval_res.recommended_entities],
                        consolidated_infractions=[dump_obj(i) for i in eval_res.consolidated_infractions],
                        extracted_metadata=[dump_obj(m) for m in eval_res.extracted_metadata]
                    )
                    st.success("¡Reevaluación completada exitosamente!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error en el análisis: {e}")

    with col_h3:
        if not read_only:
            if st.button("Editar Emergencia", use_container_width=True):
                st.session_state["show_edit_project_dialog"] = True
                st.rerun()

    with col_h4:
        if not read_only:
            if status == "activa":
                if st.button("Marcar Solucionada", use_container_width=True):
                    update_project_status(proj_id, "solucionada")
                    st.success("¡Emergencia marcada como Solucionada y archivada!")
                    st.rerun()
            else:
                if st.button("Reabrir Emergencia", use_container_width=True):
                    update_project_status(proj_id, "activa")
                    st.info("Emergencia reabierta como activa.")
                    st.rerun()

    # Evaluación en Tiempo Real: Nivel de Afectación & Riesgo para las Personas
    st.markdown("### Evaluación en Tiempo Real de la Emergencia")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**NIVEL DE AFECTACIÓN REAL:**")
        color_af = "#dc2626" if real_affectation in ["Crítica", "Critica"] else ("#d97706" if real_affectation == "Alta" else ("#eab308" if real_affectation == "Media" else "#16a34a"))
        st.markdown(f"<h3 style='color: {color_af}; margin: 0; font-weight: 800;'>{real_affectation}</h3>", unsafe_allow_html=True)
        st.caption(f"Inicial declarado: {initial_affectation}")

    with col2:
        st.markdown(f"**RIESGO REAL A PERSONAS:**")
        color_ri = "#dc2626" if real_risk == "Riesgo Inminente" else ("#d97706" if real_risk == "Riesgo Alto" else ("#eab308" if real_risk == "Riesgo Medio" else "#16a34a"))
        st.markdown(f"<h3 style='color: {color_ri}; margin: 0; font-weight: 800;'>{real_risk}</h3>", unsafe_allow_html=True)
        st.caption(f"Inicial declarado: {initial_risk}")

    with col3:
        st.markdown(f"**DETERMINACIÓN GLOBAL:**")
        st.markdown(f"<div style='background-color: var(--card-bg); border: 1px solid var(--card-border); padding: 10px; border-radius: 6px; font-weight: bold; color: var(--blue-title); text-align: center;'>{alert_level}</div>", unsafe_allow_html=True)

    if risk_eval:
        st.info(f"**Análisis Comparativo del Riesgo:** {risk_eval}")

    # Pestañas Principales
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Ficha de Emergencia",
        "Resumen & Entidades a Derivar",
        "Ubicación y Mapa",
        "Cargar / Procesar Evidencia",
        "Historial Documental"
    ])

    with tab1:
        st.markdown("#### Detalle de la Solicitud y Clasificación")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Tipo de Proyecto / Ítem:** `{project_category}`")
            st.write(f"**Dirección:** {address}")
            st.write(f"**Sector:** {sector}")
            st.write(f"**Prioridad de Atención:** `{attention_priority}`")
            st.write(f"**Nivel de Afectación Declarado:** `{initial_affectation}`")
            st.write(f"**Riesgo para las Personas Declarado:** `{initial_risk}`")
        with c2:
            st.write(f"**Tipos de Emergencia:** {', '.join(emergency_types) if emergency_types else 'No especificado'}")
            st.write(f"**Afectación:** {', '.join(affectations) if affectations else 'Ninguna'}")
            st.write(f"**Requerimiento de Recursos:** {', '.join(requirements_list) if requirements_list else 'No especificado'}")
            st.write(f"**Seguimiento:** {'SÍ (' + follow_up_resp + ')' if follow_up else 'NO'}")

        if description:
            st.markdown("**Descripción de la Solicitud:**")
            st.info(description)

        if observations:
            st.markdown("**Observaciones adicionales:**")
            st.write(observations)

    with tab2:
        st.markdown("#### Situación Consolidada de la Emergencia")
        st.write(context)

        st.markdown("---")
        st.markdown("#### Oficinas y Especialistas de Intervención Recomendados")
        if not entities:
            st.write("Aún no hay recomendaciones de derivación.")
        else:
            for ent in entities:
                ent_name = ent.get("entity_name", "") if isinstance(ent, dict) else str(ent)
                ent_reason = ent.get("reason", "") if isinstance(ent, dict) else ""
                off_cat = ent.get("office_category", "") if isinstance(ent, dict) else ""
                
                cat_badge = ""
                u_str = (ent_name + " " + off_cat).upper()
                if "SOCIAL" in u_str:
                    cat_badge = "[SOCIAL / DIDECO]"
                elif "INFRAESTRUCTURA" in u_str:
                    cat_badge = "[INFRAESTRUCTURA MUNICIPAL]"
                elif "INGENIERÍA" in u_str or "INGENIERIA" in u_str:
                    cat_badge = "[INGENIERÍA Y TRÁNSITO]"
                elif "ARQUITECTURA" in u_str:
                    cat_badge = "[ARQUITECTURA]"
                elif "HÍDRICO" in u_str or "HIDRICO" in u_str or "AGUAS DEL VALLE" in u_str:
                    cat_badge = "[ESPECIALISTA HÍDRICO / SANITARIO]"
                elif "ELÉCTRICO" in u_str or "ELECTRICO" in u_str:
                    cat_badge = "[INGENIERO ELÉCTRICO]"
                elif "CGE" in u_str:
                    cat_badge = "[CGE - RED ELÉCTRICA]"
                
                badge_html = f'<span style="color:#0284c7; font-weight:bold;">{cat_badge}</span>' if cat_badge else ''
                with st.container():
                    st.markdown(f"**• {ent_name}** {badge_html}", unsafe_allow_html=True)
                    if ent_reason:
                        st.caption(f"Motivo: {ent_reason}")

        if mitigations:
            st.markdown("#### Acciones de Mitigación Requeridas")
            for m in mitigations:
                st.markdown(f"- {m}")

        if recommendations:
            st.markdown("#### Recomendaciones Operativas para la Respuesta Municipal")
            for r in recommendations:
                st.markdown(f"1. {r}")

        if metadata:
            st.markdown("---")
            st.markdown("#### Evidencia y Parámetros Extraídos de Terreno")
            cols = st.columns(min(len(metadata), 4) if len(metadata) > 0 else 1)
            for idx, item in enumerate(metadata):
                k = item.get("key", "")
                v = item.get("value", "")
                with cols[idx % len(cols)]:
                    st.metric(label=k.upper(), value=v)

        if infractions:
            st.markdown("---")
            st.markdown(f"#### Alertas de Seguridad & Riesgos Activos ({len(infractions)})")
            for inf in infractions:
                sev = inf.get("severity", "MEDIA")
                with st.expander(f"[{sev}] {inf.get('rule_id', 'Alerta')}: {inf.get('description', '')}"):
                    st.write(f"**Evidencia en documento/foto:** {inf.get('evidence', '')}")
                    st.write(f"**Acción requerida:** {inf.get('justification', '')}")

    with tab3:
        st.markdown("#### Georeferenciación y Mapa de la Incidencia")
        st.write("Visualiza o actualiza la ubicación exacta en el mapa de terreno.")

        cur_lat = float(lat_val) if lat_val is not None else None
        cur_lng = float(lng_val) if lng_val is not None else None

        picked_lat, picked_lng = render_location_picker_map(cur_lat, cur_lng, key_prefix=f"dash_{proj_id}")

        if not read_only:
            if (picked_lat != cur_lat or picked_lng != cur_lng) and picked_lat is not None and picked_lng is not None:
                if st.button("Guardar Nuevas Coordenadas en la Emergencia", type="primary"):
                    update_project_coordinates(proj_id, picked_lat, picked_lng)
                    st.success("¡Coordenadas actualizadas exitosamente!")
                    st.rerun()

        c_lat, c_lng = st.columns(2)
        with c_lat:
            st.write(f"**Latitud Registrada:** `{lat_val if lat_val is not None else 'No asignada'}`")
        with c_lng:
            st.write(f"**Longitud Registrada:** `{lng_val if lng_val is not None else 'No asignada'}`")

    with tab4:
        st.markdown("#### Cargar y Procesar Evidencia Fotográfica o Documentos")
        if read_only:
            st.info("Modo Jefatura / Lectura: Puedes revisar las evidencias procesadas en el 'Historial Documental'. La carga de nuevos archivos está restringida a Operadores de Terreno.")
        else:
            st.write("Sube fotografías de terreno (JPG, PNG), informes de Word (.docx) o expedientes PDF. La Inteligencia Artificial analizará las imágenes y texto para actualizar el estado del evento.")

            doc_type = st.selectbox(
                "Tipo de Evidencia Ingresada",
                options=list(DOC_TYPES_MAP.keys()),
                format_func=lambda x: DOC_TYPES_MAP[x]
            )

            uploaded_files = st.file_uploader(
                "Selecciona fotografías o archivos (Soporta JPG, PNG, WEBP, DOCX, PDF, TXT)",
                type=["jpg", "jpeg", "png", "webp", "docx", "pdf", "txt"],
                accept_multiple_files=True,
                key="uploader_incident_multi"
            )

            if uploaded_files and st.button("Procesar Nuevas Evidencias", type="primary"):
                with st.spinner("Analizando imágenes/documentos y consolidando el estado de la emergencia..."):
                    try:
                        for uploaded_file in uploaded_files:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp:
                                tmp.write(uploaded_file.getbuffer())
                                tmp_path = tmp.name

                            extracted_text = extract_text_from_file(tmp_path)
                            quick_rules = evaluate_emergency_rules(extracted_text, doc_type)

                            ai_res = analyze_single_document(
                                file_content_text=extracted_text,
                                document_type=doc_type,
                                file_path=tmp_path,
                                project_data=project
                            )

                            doc_rec = add_document_to_project(proj_id, uploaded_file.name, doc_type, tmp_path)
                            if doc_rec.get("id"):
                                combined_inf = quick_rules + [dump_obj(i) for i in ai_res.infractions]
                                add_document_analysis(
                                    doc_rec["id"],
                                    ai_res.document_summary,
                                    combined_inf,
                                    [dump_obj(m) for m in ai_res.extracted_metadata]
                                )

                            eval_res = consolidate_accident_evaluation(
                                previous_context=context,
                                new_doc_summary=ai_res.document_summary,
                                new_doc_infractions=ai_res.infractions,
                                new_doc_metadata=ai_res.extracted_metadata,
                                initial_affectation_level=initial_affectation,
                                initial_people_risk=initial_risk,
                                previous_infractions=infractions,
                                previous_metadata=metadata,
                                project_data=project
                            )

                            update_project_evaluation(
                                project_id=proj_id,
                                consolidated_context=eval_res.consolidated_context,
                                initial_vs_real_risk_evaluation=eval_res.initial_vs_real_risk_evaluation,
                                real_affectation_level=eval_res.real_affectation_level,
                                real_people_risk=eval_res.real_people_risk,
                                overall_alert_level=eval_res.overall_alert_level,
                                mitigation_actions=eval_res.mitigation_actions,
                                action_recommendations=eval_res.action_recommendations,
                                recommended_entities=[dump_obj(e) for e in eval_res.recommended_entities],
                                consolidated_infractions=[dump_obj(i) for i in eval_res.consolidated_infractions],
                                extracted_metadata=[dump_obj(m) for m in eval_res.extracted_metadata]
                            )
                            context = eval_res.consolidated_context

                        st.success("¡Evidencias procesadas y emergencia actualizada exitosamente!")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Error procesando la evidencia: {e}")

    with tab5:
        st.markdown("#### Registro Histórico de Evidencias e Imágenes")
        docs = list_project_documents(proj_id)
        if not docs:
            st.info("Aún no se han cargado evidencias para esta emergencia.")
        else:
            for d in docs:
                st.markdown(f"""
                    <div style="background-color: var(--card-bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--card-border); margin-bottom: 0.8rem;">
                        <strong style="color: var(--text-primary);">Archivo: {d.get('file_name')}</strong> | Tipo: <em style="color: var(--blue-title);">{DOC_TYPES_MAP.get(d.get('document_type'), d.get('document_type'))}</em>
                        <br/><small style="color: var(--text-secondary);">Cargado en: {d.get('uploaded_at')}</small>
                    </div>
                """, unsafe_allow_html=True)