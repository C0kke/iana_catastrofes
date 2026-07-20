import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
from datetime import datetime
from fpdf import FPDF

class ExecutivePDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(2, 132, 199)
        self.cell(0, 10, 'IANA - EMERGENCIA | INFORME TÉCNICO EJECUTIVO', border=False, new_x="LMARGIN", new_y="NEXT", align='L')
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(100, 116, 139)
        self.cell(0, 5, 'Centro de Mando Digital & Gestión del Riesgo - Región de Coquimbo', border=False, new_x="LMARGIN", new_y="NEXT", align='L')
        self.line(10, 26, 200, 26)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}} - Documento de Control IANA - EMERGENCIA', align='C')

def sanitize_pdf_text(text: str) -> str:
    """Reemplaza caracteres especiales para compatibilidad limpia con FPDF."""
    if not text:
        return ""
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N", "°": " deg", "–": "-", "—": "-",
        "“": '"', "”": '"', "’": "'", "⛔": "[CORTADA]"
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pdf_report(entity_key: str, commune_filter: str, projects: list, critical_pts: list) -> bytes:
    pdf = ExecutivePDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M hrs")
    
    entity_titles = {
        "MOP": "MINISTERIO DE OBRAS PÚBLICAS / VIALIDAD",
        "CGE": "COMPAÑÍA GENERAL DE ELECTRICIDAD (CGE)",
        "AGUAS": "AGUAS DEL VALLE - SANAMIENTO Y AGUA POTABLE",
        "SENAPRED": "SENAPRED / COGRID MUNICIPAL (INFORME ALFA)"
    }
    title_str = entity_titles.get(entity_key, "INFORME EJECUTIVO REGIONAL")
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 7, sanitize_pdf_text(f"DESTINATARIO: {title_str}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, sanitize_pdf_text(f"ZONA EVALUADA: Comuna de {commune_filter.upper()}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, sanitize_pdf_text(f"FECHA / HORA EMISIÓN: {now_str}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    
    if commune_filter != "Todas las Comunas Afectadas":
        p_filt = [p for p in projects if p.get("commune") == commune_filter]
        cp_filt = [cp for cp in critical_pts if cp.get("commune") == commune_filter]
    else:
        p_filt = projects
        cp_filt = critical_pts
        
    act_p = [p for p in p_filt if p.get("status", "activa") == "activa"]
    act_cp = [cp for cp in cp_filt if cp.get("status", "activo") == "activo"]
    
    pdf.set_font('Helvetica', 'B', 11)

    pdf.set_text_color(2, 132, 199)
    
    # 1. EVALUACIÓN Y RESUMEN OPERATIVO POR ENTIDAD
    if entity_key == "MOP":
        pdf.cell(0, 7, sanitize_pdf_text("1. EVALUACIÓN DE CONECTIVIDAD VIAL Y RUTAS ESTRUCTURANTES"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(51, 65, 85)
        
        road_cuts = [cp for cp in act_cp if cp.get("point_type") in ["ruta_cortada", "socavon", "derrumbe"]]
        mop_projects = [p for p in act_p if p.get("project_category") in ["Caminos y Carreteras", "Puentes", "Grandes Ítems"] or p.get("project_type") in ["socavon", "derrumbe", "remocion_masa", "dano_pavimento"]]
        isolation_level = "SEVERO / CONEXIÓN IMPOSIBLE" if len(road_cuts) >= 2 else ("RESTRINGIDO / SOLO 4X4" if len(road_cuts) == 1 else "CONTROLADO")
        
        desc = (
            f"Puntos Críticos Viales y Rutas Cortadas: {len(road_cuts)} eventos de alta severidad.\n"
            f"Emergencias Registradas en Carreteras/Vías: {len(mop_projects)} casos activos.\n"
            f"Diagnóstico Cualitativo de Conectividad: {isolation_level}.\n"
            f"Requerimiento Prioritario: Despliegue de maquinaria pesada MOP/Vialidad (retroexcavadoras, motoniveladoras, camiones tolva)."
        )
        pdf.multi_cell(0, 5, sanitize_pdf_text(desc))
        pdf.ln(4)
        
        # 2. PUNTOS CRÍTICOS (SOLO MOP Y SENAPRED)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(2, 132, 199)
        pdf.cell(0, 7, sanitize_pdf_text("2. RUTAS CORTADAS Y PUNTOS CRÍTICOS REGISTRADOS"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(15, 23, 42)
        if not act_cp:
            pdf.cell(0, 6, sanitize_pdf_text("Sin rutas cortadas registradas actualmente."), new_x="LMARGIN", new_y="NEXT")
        else:
            for cp in act_cp:
                line_str = f"- [{cp.get('severity', 'CRITICO')}] {cp.get('name', 'Punto Critico')} | Sector: {cp.get('sector', 'N/A')} ({cp.get('commune', '')}) - {cp.get('description', '')}"
                pdf.multi_cell(0, 5, sanitize_pdf_text(line_str))
                pdf.ln(1)
        pdf.ln(4)
        
        # 3. CATASTRO DE EMERGENCIAS VIALES
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(2, 132, 199)
        pdf.cell(0, 7, sanitize_pdf_text("3. CATASTRO DE EMERGENCIAS VIALES ACTIVAS (MOP / VIALIDAD)"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(15, 23, 42)
        if not mop_projects:
            pdf.cell(0, 6, sanitize_pdf_text("Sin emergencias viales específicas activas en terreno."), new_x="LMARGIN", new_y="NEXT")
        else:
            for p in mop_projects:
                line_str = f"- {p.get('name', 'Emergencia')} | Sector: {p.get('sector', 'N/A')} | Afectacion: {p.get('real_affectation_level', 'Media')} | Riesgo Personas: {p.get('real_people_risk', 'Medio')}"
                pdf.multi_cell(0, 5, sanitize_pdf_text(line_str))
                pdf.ln(1)

    elif entity_key == "CGE":
        pdf.cell(0, 7, sanitize_pdf_text("1. RESUMEN DE AFECTACIÓN EN RED ELÉCTRICA Y ALUMBRADO"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(51, 65, 85)

        def is_cge_issue(p):
            affs = str(p.get("affectations", [])).lower()
            desc_t = (p.get("description", "") + " " + p.get("name", "")).lower()
            ptype = str(p.get("project_type", "")).lower()
            keywords = ["electrica", "luz", "alumbrado", "poste", "cable", "suministro", "transformador", "caida_poste", "dano_alumbrado"]
            return any(k in affs or k in desc_t or k in ptype for k in keywords)

        elec_p = [p for p in act_p if is_cge_issue(p)]
        desc = (
            f"Total Emergencias Delegadas a CGE (Cortes de Suministro y Postación): {len(elec_p)} casos activos.\n"
            f"Diagnóstico de Riesgo: Postación caída, cortes de energía en vía pública y líneas de media/baja tensión expuestas."
        )
        pdf.multi_cell(0, 5, sanitize_pdf_text(desc))
        pdf.ln(4)
        
        # 2. CATASTRO DE EMERGENCIAS ELÉCTRICAS (SIN RUTAS CORTADAS)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(2, 132, 199)
        pdf.cell(0, 7, sanitize_pdf_text("2. CATASTRO DE EMERGENCIAS ELÉCTRICAS ASIGNADAS A CGE"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(15, 23, 42)
        if not elec_p:
            pdf.cell(0, 6, sanitize_pdf_text("Sin emergencias eléctricas o de postación asignadas actualmente en esta zona."), new_x="LMARGIN", new_y="NEXT")
        else:
            for p in elec_p:
                line_str = f"- {p.get('name', 'Emergencia Electrica')} | Sector: {p.get('sector', 'N/A')} | Afectacion: {p.get('real_affectation_level', 'Media')} | Riesgo Personas: {p.get('real_people_risk', 'Medio')}"
                pdf.multi_cell(0, 5, sanitize_pdf_text(line_str))
                pdf.ln(1)

    elif entity_key == "AGUAS":
        pdf.cell(0, 7, sanitize_pdf_text("1. RESUMEN DE AFECTACIÓN SANITARIA Y RED DE AGUA POTABLE"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(51, 65, 85)

        def is_aguas_issue(p):
            affs = str(p.get("affectations", [])).lower()
            desc_t = (p.get("description", "") + " " + p.get("name", "")).lower()
            ptype = str(p.get("project_type", "")).lower()
            keywords = ["agua", "alcantarillado", "matriz", "tuberia", "tubería", "colector", "grifo", "sanitari", "rotura_matriz", "anegamiento", "inundacion"]
            return any(k in affs or k in desc_t or k in ptype for k in keywords)

        water_p = [p for p in act_p if is_aguas_issue(p)]
        desc = (
            f"Total Emergencias Delegadas a Aguas del Valle (Matrices y Colectores): {len(water_p)} casos activos.\n"
            f"Prioridad Operativa: Atención inmediata a roturas de matriz de agua potable, desborde de colectores sanitarios y anegamiento de viviendas."
        )
        pdf.multi_cell(0, 5, sanitize_pdf_text(desc))
        pdf.ln(4)
        
        # 2. CATASTRO DE EMERGENCIAS SANITARIAS (SIN RUTAS CORTADAS)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(2, 132, 199)
        pdf.cell(0, 7, sanitize_pdf_text("2. CATASTRO DE EMERGENCIAS SANITARIAS ASIGNADAS A AGUAS DEL VALLE"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(15, 23, 42)
        if not water_p:
            pdf.cell(0, 6, sanitize_pdf_text("Sin emergencias de agua potable o red sanitaria asignadas actualmente en esta zona."), new_x="LMARGIN", new_y="NEXT")
        else:
            for p in water_p:
                line_str = f"- {p.get('name', 'Emergencia Sanitaria')} | Sector: {p.get('sector', 'N/A')} | Afectacion: {p.get('real_affectation_level', 'Media')} | Riesgo Personas: {p.get('real_people_risk', 'Medio')}"
                pdf.multi_cell(0, 5, sanitize_pdf_text(line_str))
                pdf.ln(1)

    else: # SENAPRED / INFORME ALFA
        pdf.cell(0, 7, sanitize_pdf_text("1. INFORME CONSOLIDADO ALFA - EVALUACIÓN COGRID MUNICIPAL"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(51, 65, 85)
        desc = (
            f"Total Emergencias Activas en Catastro: {len(act_p)}\n"
            f"Total Rutas Cortadas / Puntos Críticos: {len(act_cp)}\n"
            f"Estado Operativo Comunal: ACTIVACIÓN TOTAL DE CUADRILLAS Y COGRID REGIONAL."
        )
        pdf.multi_cell(0, 5, sanitize_pdf_text(desc))
        pdf.ln(4)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(2, 132, 199)
        pdf.cell(0, 7, sanitize_pdf_text("2. RUTAS CORTADAS Y PUNTOS CRÍTICOS REGISTRADOS"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(15, 23, 42)
        if not act_cp:
            pdf.cell(0, 6, sanitize_pdf_text("Sin rutas cortadas registradas actualmente."), new_x="LMARGIN", new_y="NEXT")
        else:
            for cp in act_cp:
                line_str = f"- [{cp.get('severity', 'CRITICO')}] {cp.get('name', 'Punto Critico')} | Sector: {cp.get('sector', 'N/A')} ({cp.get('commune', '')}) - {cp.get('description', '')}"
                pdf.multi_cell(0, 5, sanitize_pdf_text(line_str))
                pdf.ln(1)
        pdf.ln(4)

        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(2, 132, 199)
        pdf.cell(0, 7, sanitize_pdf_text("3. CATASTRO GENERAL DE EMERGENCIAS ACTIVAS EN TERRENO"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(15, 23, 42)
        if not act_p:
            pdf.cell(0, 6, sanitize_pdf_text("Sin emergencias activas registradas en terreno."), new_x="LMARGIN", new_y="NEXT")
        else:
            for p in act_p:
                line_str = f"- {p.get('name', 'Emergencia')} | Sector: {p.get('sector', 'N/A')} | Afectacion: {p.get('real_affectation_level', 'Media')} | Riesgo Personas: {p.get('real_people_risk', 'Medio')}"
                pdf.multi_cell(0, 5, sanitize_pdf_text(line_str))
                pdf.ln(1)

    pdf.ln(12)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 5, sanitize_pdf_text("____________________________________________________"), new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(0, 5, sanitize_pdf_text("FIRMA / TIMBRE JEFATURA DE OPERACIONES Y GESTIÓN DEL RIESGO"), new_x="LMARGIN", new_y="NEXT", align='C')
    
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()

def render_commune_impact_dashboard(all_projects: List[Dict[str, Any]], critical_points: List[Dict[str, Any]] = []):
    st.markdown("### Centro de Mando Ejecutivo - Impacto Comunal y Matriz de Riesgo")
    st.caption("Panel de control gerencial para el análisis multimodal de afectación en infraestructura, servicios básicos y nivel de vulnerabilidad poblacional.")

    projects_with_commune = [p for p in all_projects if p.get("commune")]
    communes_set = sorted(list(set(p.get("commune") for p in projects_with_commune)))

    if not communes_set:
        st.info("No se han registrado emergencias georreferenciadas o asociadas a comunas en el sistema actualmente.")
        return

    col_sel, col_blank = st.columns([1.8, 2.2])
    with col_sel:
        selected_commune = st.selectbox(
            "Filtrar por Comuna Afectada",
            options=["Todas las Comunas Afectadas"] + communes_set,
            index=0
        )

    filtered_projects = (
        projects_with_commune if selected_commune == "Todas las Comunas Afectadas"
        else [p for p in projects_with_commune if p.get("commune") == selected_commune]
    )

    # 1. KPIs Críticos del Catastro
    c_active = [p for p in filtered_projects if (p.get("status") or "activa") == "activa"]
    c_critical = [p for p in c_active if p.get("real_affectation_level") in ["Crítica", "Critica"] or p.get("real_people_risk") == "Riesgo Inminente"]
    
    electric_count = sum(1 for p in filtered_projects if any("Electrica" in str(x) or "Luz" in str(x) or "Alumbrado" in str(x) for x in (p.get("affectations") or [])))
    water_count = sum(1 for p in filtered_projects if any("Agua" in str(x) or "Alcantarillado" in str(x) for x in (p.get("affectations") or [])))
    req_machinery = sum(1 for p in filtered_projects if len(p.get("requirements_list") or []) > 0)

    st.markdown("<br/>", unsafe_allow_html=True)
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        st.metric(label="COMUNAS EVALUADAS", value=len(communes_set) if selected_commune == "Todas las Comunas Afectadas" else 1)
    with k2:
        st.metric(label="EMERGENCIAS EN ZONA", value=len(filtered_projects))
    with k3:
        st.metric(label="RIESGO INMINENTE", value=len(c_critical))
    with k4:
        st.metric(label="RED ELÉCTRICA CGE", value=electric_count)
    with k5:
        st.metric(label="AGUAS DEL VALLE", value=water_count)
    with k6:
        st.metric(label="SOLICITUD DE MAQUINARIA", value=req_machinery)

    st.markdown("---")

    # 2. Fila 1 de Gráficos: Categoría, Servicios y Riesgo para las Personas
    st.markdown("#### Distribución de Afectación por Categoría y Servicios Básicos")
    g1, g2, g3 = st.columns(3)

    with g1:
        cat_counts = {}
        for p in filtered_projects:
            cat = p.get("project_category") or "Infraestructura Pública"
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
        
        df_cat = pd.DataFrame(list(cat_counts.items()), columns=["Categoría", "Cantidad"])
        fig_pie1 = px.pie(
            df_cat,
            names="Categoría",
            values="Cantidad",
            title="Categoría de Emergencia",
            color_discrete_sequence=px.colors.qualitative.Set2,
            hole=0.4
        )
        fig_pie1.update_layout(margin=dict(t=40, b=0, l=0, r=0), showlegend=True, height=280)
        st.plotly_chart(fig_pie1, use_container_width=True)

    with g2:
        affectation_counts = {}
        for p in filtered_projects:
            aff_list = p.get("affectations") or []
            if isinstance(aff_list, list):
                for aff_item in aff_list:
                    if aff_item:
                        affectation_counts[aff_item] = affectation_counts.get(aff_item, 0) + 1
            elif isinstance(aff_list, str) and aff_list:
                affectation_counts[aff_list] = affectation_counts.get(aff_list, 0) + 1

        if affectation_counts:
            df_aff = pd.DataFrame(list(affectation_counts.items()), columns=["Servicio", "Frecuencia"])
            fig_pie2 = px.pie(
                df_aff,
                names="Servicio",
                values="Frecuencia",
                title="Servicios Afectados",
                color_discrete_sequence=px.colors.sequential.Teal,
                hole=0.4
            )
            fig_pie2.update_layout(margin=dict(t=40, b=0, l=0, r=0), showlegend=True, height=280)
            st.plotly_chart(fig_pie2, use_container_width=True)
        else:
            st.info("Sin registros de servicios afectados.")

    with g3:
        risk_counts = {}
        for p in filtered_projects:
            r_val = p.get("real_people_risk") or p.get("people_risk") or "Riesgo Medio"
            risk_counts[r_val] = risk_counts.get(r_val, 0) + 1

        df_risk = pd.DataFrame(list(risk_counts.items()), columns=["Nivel de Riesgo", "Cantidad"])
        colors_map = {
            "Riesgo Inminente": "#dc2626",
            "Riesgo Alto": "#d97706",
            "Riesgo Medio": "#eab308",
            "Riesgo Bajo": "#16a34a",
            "Sin riesgo": "#0284c7"
        }
        fig_pie3 = px.pie(
            df_risk,
            names="Nivel de Riesgo",
            values="Cantidad",
            title="Riesgo para las Personas",
            color="Nivel de Riesgo",
            color_discrete_map=colors_map,
            hole=0.4
        )
        fig_pie3.update_layout(margin=dict(t=40, b=0, l=0, r=0), showlegend=True, height=280)
        st.plotly_chart(fig_pie3, use_container_width=True)

    st.markdown("---")

    # 3. Fila 2: Análisis Comparativo por Comuna y Demanda de Recursos
    st.markdown("#### Análisis Comparativo de Respuesta Municipal y Requerimiento de Maquinaria")
    b1, b2 = st.columns(2)

    with b1:
        st.markdown("**Incidencias por Nivel de Afectación Real**")
        aff_levels = {}
        for p in filtered_projects:
            lvl = p.get("real_affectation_level") or p.get("affectation_level") or "Media"
            aff_levels[lvl] = aff_levels.get(lvl, 0) + 1
        
        df_lvl = pd.DataFrame(list(aff_levels.items()), columns=["Nivel de Afectación", "Total Emergencias"])
        fig_bar = px.bar(
            df_lvl,
            x="Nivel de Afectación",
            y="Total Emergencias",
            color="Nivel de Afectación",
            color_discrete_map={"Crítica": "#dc2626", "Critica": "#dc2626", "Alta": "#d97706", "Media": "#0284c7", "Baja": "#16a34a"},
            text_auto=True
        )
        fig_bar.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=300, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with b2:
        st.markdown("**Demandas de Recurso Técnico y Maquinaria Pesada**")
        req_counts = {}
        for p in filtered_projects:
            req_l = p.get("requirements_list") or []
            if isinstance(req_l, list):
                for item in req_l:
                    if item:
                        req_counts[item] = req_counts.get(item, 0) + 1
            elif isinstance(req_l, str) and req_l:
                req_counts[req_l] = req_counts.get(req_l, 0) + 1

        if req_counts:
            df_req = pd.DataFrame(list(req_counts.items()), columns=["Recurso Requerido", "Solicitudes"]).sort_values(by="Solicitudes", ascending=True)
            fig_req = px.bar(
                df_req,
                x="Solicitudes",
                y="Recurso Requerido",
                orientation="h",
                color_discrete_sequence=["#0284c7"],
                text_auto=True
            )
            fig_req.update_layout(margin=dict(t=20, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig_req, use_container_width=True)
        else:
            st.info("Sin solicitudes de maquinaria registradas.")

    st.markdown("---")

    # 4. Generación y Exportación de Informes Ejecutivos por Entidad en PDF
    st.markdown("#### Generación y Exportación de Informes Ejecutivos en PDF")
    st.caption("Selecciona la entidad técnico-operativa de destino para exportar un informe oficial en formato PDF listo para envío e impresión.")

    col_e1, col_e2 = st.columns([2, 1])
    with col_e1:
        entity_choice = st.selectbox(
            "Entidad Destinataria del Informe",
            options=[
                "MOP / Dirección de Vialidad (Conectividad y Rutas Cortadas)",
                "CGE (Cortes de Suministro Eléctrico y Postación)",
                "Aguas del Valle (Matrices, Tuberías y Red Sanitaria)",
                "SENAPRED / Municipalidad (Informe ALFA Ejecutivo)"
            ],
            key="pdf_entity_selector"
        )
    
    key_map = {
        "MOP / Dirección de Vialidad (Conectividad y Rutas Cortadas)": "MOP",
        "CGE (Cortes de Suministro Eléctrico y Postación)": "CGE",
        "Aguas del Valle (Matrices, Tuberías y Red Sanitaria)": "AGUAS",
        "SENAPRED / Municipalidad (Informe ALFA Ejecutivo)": "SENAPRED"
    }
    sel_key = key_map.get(entity_choice, "SENAPRED")

    with col_e2:
        st.markdown("<br/>", unsafe_allow_html=True)
        pdf_bytes = generate_pdf_report(
            entity_key=sel_key,
            commune_filter=selected_commune,
            projects=all_projects,
            critical_pts=critical_points
        )
        file_commune_str = selected_commune.replace(" ", "_")
        filename_map = {
            "MOP": f"Informe_MOP_Vialidad_{file_commune_str}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            "CGE": f"Informe_CGE_Electrica_{file_commune_str}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            "AGUAS": f"Informe_Aguas_del_Valle_{file_commune_str}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            "SENAPRED": f"Informe_SENAPRED_ALFA_{file_commune_str}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        }
        custom_filename = filename_map.get(sel_key, f"Informe_{sel_key}_{file_commune_str}.pdf")

        st.download_button(
            label="Descargar Informe en PDF",
            data=pdf_bytes,
            file_name=custom_filename,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

    st.markdown("---")

    st.markdown("#### Matriz de Monitoreo por Comuna Afectada")

    for com_name in (communes_set if selected_commune == "Todas las Comunas Afectadas" else [selected_commune]):
        com_projs = [p for p in projects_with_commune if p.get("commune") == com_name]
        if not com_projs:
            continue

        com_active = [p for p in com_projs if p.get("status", "activa") == "activa"]
        com_resolved = [p for p in com_projs if p.get("status", "activa") in ["tratada", "solucionada"]]
        
        sectors = list(set(p.get("sector") for p in com_projs if p.get("sector")))
        sectors_str = ", ".join(sectors) if sectors else "Sin sector especificado"

        cats = list(set(p.get("project_category", "Infraestructura") for p in com_projs))
        cats_str = ", ".join(cats)

        max_aff = "Media"
        for p in com_projs:
            p_aff = p.get("real_affectation_level", p.get("affectation_level", "Media"))
            if p_aff in ["Crítica", "Critica"]:
                max_aff = "CRÍTICA"
                break
            elif p_aff == "Alta":
                max_aff = "ALTA"

        badge_color = "#dc2626" if max_aff == "CRÍTICA" else ("#d97706" if max_aff == "ALTA" else "#0284c7")

        with st.expander(f"Comuna de {com_name.upper()} - {len(com_active)} Activas / {len(com_resolved)} Resueltas - Severidad Máxima: {max_aff}"):
            st.markdown(f"""
                <div style="background-color: var(--card-bg); padding: 1.2rem; border-radius: 8px; border: 1px solid var(--card-border); margin-bottom: 0.8rem;">
                    <span style="background-color: {badge_color}; color: #ffffff; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.8rem;">
                        AFECTACIÓN MÁXIMA: {max_aff}
                    </span>
                    <h3 style="color: var(--blue-title); margin: 8px 0 4px 0;">Comuna de {com_name}</h3>
                    <p style="margin: 0; font-size: 0.95rem;"><strong>Sectores Afectados:</strong> {sectors_str}</p>
                    <p style="margin: 4px 0 0 0; font-size: 0.95rem;"><strong>Tipos de Proyectos Comprometidos:</strong> {cats_str}</p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("**Emergencias Registradas en esta Comuna:**")
            for cp in com_projs:
                cp_name = cp.get("name") or "Emergencia"
                cp_aff = cp.get("real_affectation_level") or cp.get("affectation_level") or "Media"
                cp_risk = cp.get("real_people_risk") or cp.get("people_risk") or "Riesgo Medio"
                cp_address = cp.get("address") or ""
                cp_status = (cp.get("status") or "activa").upper()

                st.write(f"- **{cp_name}** ({cp_status}) | Dirección: {cp_address} | Afectación: `{cp_aff}` | Riesgo Personas: `{cp_risk}`")