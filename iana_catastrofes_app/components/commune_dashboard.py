import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any

def render_commune_impact_dashboard(all_projects: List[Dict[str, Any]]):
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

    # 1. KPIs Críticos del Catastro (6 Métricas de Alta Visibilidad)
    c_active = [p for p in filtered_projects if p.get("status", "activa") == "activa"]
    c_critical = [p for p in c_active if p.get("real_affectation_level") in ["Crítica", "Critica"] or p.get("real_people_risk") == "Riesgo Inminente"]
    c_high = [p for p in c_active if p.get("real_affectation_level") == "Alta" or p.get("real_people_risk") == "Riesgo Alto"]
    
    # Contar emergencias de agua y luz
    electric_count = sum(1 for p in filtered_projects if any("Electrica" in str(x) or "Luz" in str(x) or "Alumbrado" in str(x) for x in p.get("affectations", [])))
    water_count = sum(1 for p in filtered_projects if any("Agua" in str(x) or "Alcantarillado" in str(x) for x in p.get("affectations", [])))
    req_machinery = sum(1 for p in filtered_projects if len(p.get("requirements_list", [])) > 0)

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
        st.metric(label="AGUA / ALCANTARILLADO", value=water_count)
    with k6:
        st.metric(label="SOLICITUD DE MAQUINARIA", value=req_machinery)

    st.markdown("---")

    # 2. Fila 1 de Gráficos: Gráficos de Torta y Donut de Impacto Multimodal
    st.markdown("#### Distribución de Afectación por Categoría y Servicios Básicos")
    g1, g2, g3 = st.columns(3)

    # Gráfico de Torta 1: Tipos de Proyecto Comprometidos
    with g1:
        cat_counts = {}
        for p in filtered_projects:
            cat = p.get("project_category", "Infraestructura Pública")
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

    # Gráfico de Torta 2: Servicios e Infraestructura Afectada
    with g2:
        affectation_counts = {}
        for p in filtered_projects:
            aff_list = p.get("affectations", [])
            if isinstance(aff_list, list):
                for aff_item in aff_list:
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
            st.info("Sin registros de servicios específicos.")

    # Gráfico de Torta 3: Riesgo para la Población
    with g3:
        risk_counts = {}
        for p in filtered_projects:
            r_val = p.get("real_people_risk", p.get("people_risk", "Riesgo Medio"))
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
            lvl = p.get("real_affectation_level", p.get("affectation_level", "Media"))
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
            req_l = p.get("requirements_list", [])
            if isinstance(req_l, list):
                for item in req_l:
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

    # 4. Matriz Comunal Ejecutiva (Expander Cards con Resumen de Terreno)
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
                cp_name = cp.get("name", "Emergencia")
                cp_aff = cp.get("real_affectation_level", cp.get("affectation_level", "Media"))
                cp_risk = cp.get("real_people_risk", cp.get("people_risk", "Riesgo Medio"))
                cp_address = cp.get("address", "")
                cp_status = cp.get("status", "activa").upper()

                st.write(f"- **{cp_name}** ({cp_status}) | Dirección: {cp_address} | Afectación: `{cp_aff}` | Riesgo Personas: `{cp_risk}`")
