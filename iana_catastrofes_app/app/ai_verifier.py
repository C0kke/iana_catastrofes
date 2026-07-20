from __future__ import annotations

import os
import io
import re
import json
from google import genai
from google.genai import types
import instructor
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

#Modelo y modelo de reserva
#DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_MODEL = "gemini-3.1-flash-lite"

try:
    genai_client = genai.Client(api_key=api_key) if api_key else genai.Client()
    client = instructor.from_genai(genai_client, mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS)
except Exception as e:
    client = None
    print(f"Error inicializando el cliente Gemini: {e}")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFORME_ALFA_PATH = os.path.join(BASE_DIR, "knowledge", "informe_alfa.json")

def dump_obj(item: Any) -> Dict[str, Any]:
    """Serializa de forma segura objetos Pydantic o diccionarios."""
    if hasattr(item, "model_dump"):
        return item.model_dump()
    elif isinstance(item, dict):
        return item
    elif hasattr(item, "dict"):
        return item.dict()
    return {"val": str(item)}

def build_project_context(project_data: Optional[Dict[str, Any]] = None) -> str:
    """Construye el contexto operativo a partir de los datos propios de la emergencia."""
    if not project_data:
        return "No hay datos de la emergencia disponibles."
    lines = []
    if project_data.get("name"):
        lines.append(f"Nombre: {project_data['name']}")
    if project_data.get("sector"):
        lines.append(f"Sector: {project_data['sector']}")
    if project_data.get("commune"):
        lines.append(f"Comuna: {project_data['commune']}")
    if project_data.get("region"):
        lines.append(f"Región: {project_data['region']}")
    if project_data.get("project_category"):
        lines.append(f"Categoría: {project_data['project_category']}")
    et = project_data.get("emergency_types", [])
    if et:
        lines.append(f"Tipos de Emergencia: {', '.join(et) if isinstance(et, list) else et}")
    if project_data.get("description"):
        lines.append(f"Descripción: {project_data['description']}")
    if project_data.get("affectation_level"):
        lines.append(f"Nivel de Afectación Declarado: {project_data['affectation_level']}")
    if project_data.get("people_risk"):
        lines.append(f"Riesgo Personas Declarado: {project_data['people_risk']}")
    aff = project_data.get("affectations", [])
    if aff:
        lines.append(f"Afectaciones: {', '.join(aff) if isinstance(aff, list) else aff}")
    req = project_data.get("requirements_list", [])
    if req:
        lines.append(f"Requerimientos: {', '.join(req) if isinstance(req, list) else req}")
    if project_data.get("attention_priority"):
        lines.append(f"Prioridad de Atención: {project_data['attention_priority']}")
    if project_data.get("observations"):
        lines.append(f"Observaciones: {project_data['observations']}")
    if project_data.get("follow_up"):
        resp = project_data.get("follow_up_responsible", "")
        lines.append(f"Seguimiento: Sí{' - ' + resp if resp else ''}")
    return "\n".join(lines) if lines else "Sin datos de la emergencia."

class MetadataItem(BaseModel):
    key: str = Field(description="Nombre del parámetro (ej: 'tipo_proyecto', 'sector', 'nivel_afectacion', 'vias_bloqueadas', 'danos_visibles', 'recursos_requeridos')")
    value: str = Field(description="Valor del parámetro (ej: 'Caminos y Carreteras', 'Sector Norte', 'Crítico', '2 Pistas', 'Rotura de cañería', 'Camión Aljibe')")

class Infraction(BaseModel):
    rule_id: str = Field(
        description="Identificador o categoría del riesgo (ej. 'Riesgo Electrocución / CGE', 'Desborde Colector / Especialista Hídrico', 'Daño Estructural / Arquitectura')"
    )
    description: str = Field(
        description="Descripción detallada del riesgo, daño o falla detectada"
    )
    severity: str = Field(
        description="Severidad de la alerta: 'CRÍTICA' (Peligro inminente / vida), 'ALTA' (Riesgo alto / estructura), 'MEDIA' (Afectación moderada) o 'BAJA' (Observación menor)"
    )
    evidence: str = Field(
        description="Dato, texto u observación visual exacta extraída de la evidencia"
    )
    justification: str = Field(
        description="Explicación de las acciones y requerimientos de mitigación necesarios"
    )

class DocumentSpecificAnalysis(BaseModel):
    """Análisis individual de un documento o fotografía de la emergencia"""
    document_summary: str = Field(
        description="Resumen conciso de los antecedentes o elementos visuales/técnicos observados en este archivo (máximo 300 palabras)."
    )
    is_valid_architectural_doc: bool = Field(
        description="Indica si el archivo guarda relación directa con una emergencia urbana/vial/climática (fotografías de daños, parte policial, informe Word, ficha SAMU, etc.)."
    )
    detected_affectation_level: str = Field(
        description="Nivel de afectación inferido en este archivo: 'Baja', 'Media', 'Alta' o 'Crítica'."
    )
    detected_people_risk: str = Field(
        description="Riesgo para las personas inferido en este archivo: 'Sin riesgo', 'Riesgo Bajo', 'Riesgo Medio', 'Riesgo Alto' o 'Riesgo Inminente'."
    )
    infractions: List[Infraction] = Field(
        description="Lista de alertas o riesgos detectados en este archivo/fotografía."
    )
    extracted_metadata: List[MetadataItem] = Field(
        default_factory=list,
        description="Lista de datos de campo y parámetros clave extraídos."
    )

class EntityRecommendation(BaseModel):
    office_category: str = Field(
        description="Categoría o tipo de oficina/especialista que interviene obligatoriamente. Debe ser uno o más de los siguientes: 'Social', 'Infraestructura', 'Ingeniería', 'Arquitectura', 'Especialista Hídrico', 'Ingeniero Eléctrico', 'CGE', 'Aguas del Valle', 'SENAPRED / Emergencias'."
    )
    entity_name: str = Field(
        description="Nombre formal de la unidad o profesional (ej: 'Social (DIDECO / Asistencia Social)', 'Infraestructura Municipal (Obras)', 'Ingeniería (Tránsito y Vialidad)', 'Arquitectura (Edificación)', 'Especialista Hídrico / Aguas del Valle', 'Ingeniero Eléctrico / CGE')."
    )
    reason: str = Field(
        description="Motivo específico y justificación operativa del requerimiento de intervención de dicha oficina."
    )

class ConsolidatedProjectEvaluation(BaseModel):
    """Evaluación acumulativa en tiempo real basada en Nivel de Afectación y Riesgo para las Personas (Sin Porcentajes)"""
    consolidated_context: str = Field(
        description="Resumen cronológico acumulado de la emergencia en la Región de Coquimbo. Unifica los datos iniciales con la nueva evidencia."
    )
    initial_vs_real_risk_evaluation: str = Field(
        description="Evaluación comparativa: Contrasta el Nivel de Afectación y Riesgo a Personas declarados inicialmente con los valores REALES observados en terreno."
    )
    real_affectation_level: str = Field(
        description="Nivel de Afectación REAL determinado tras analizar las evidencias en terreno: 'Baja', 'Media', 'Alta' o 'Crítica'."
    )
    real_people_risk: str = Field(
        description="Riesgo REAL para las Personas determinado tras analizar las evidencias: 'Sin riesgo', 'Riesgo Bajo', 'Riesgo Medio', 'Riesgo Alto' o 'Riesgo Inminente'."
    )
    overall_alert_level: str = Field(
        description="Determinación global de alerta combinando Afectación y Riesgo a Personas (ej: 'CRÍTICA - RIESGO INMINENTE', 'ALTA - RIESGO ALTO', 'MEDIA - RIESGO MEDIO', 'BAJA - SIN RIESGO'). JAMÁS ENTREGUES PORCENTAJES."
    )
    mitigation_actions: List[str] = Field(
        description="Lista de acciones de mitigación concretas requeridas para contener la contingencia."
    )
    action_recommendations: List[str] = Field(
        description="Recomendaciones operativas paso a paso para desplegar las cuadrillas municipales."
    )
    recommended_entities: List[EntityRecommendation] = Field(
        description="Lista de oficinas y profesionales especializados que deben intervenir (Social, Infraestructura, Ingeniería, Arquitectura, Especialista Hídrico, Ingeniero Eléctrico, CGE, Aguas del Valle)."
    )
    consolidated_infractions: List[Infraction] = Field(
        description="Lista acumulada de alertas de riesgo activas."
    )
    extracted_metadata: List[MetadataItem] = Field(
        default_factory=list,
        description="Lista de parámetros unificados de la emergencia."
    )

def analyze_single_document(
    file_content_text: str,
    document_type: str,
    file_path: Optional[str] = None,
    project_data: Optional[Dict[str, Any]] = None,
    model_name: str = DEFAULT_MODEL
) -> DocumentSpecificAnalysis:
    """Analiza un documento de texto, Word o fotografía usando Gemini Multimodal + Instructor.
    El contexto proviene exclusivamente de los datos de la emergencia registrada por el usuario."""
    if not client:
        raise RuntimeError("El cliente de Gemini no está configurado. Revisa GEMINI_API_KEY.")

    # Contexto basado en los datos propios de la emergencia, NO en documentos externos
    emergency_context = build_project_context(project_data)

    content_list = []
    prompt_text = f"""
    Eres un Evaluador Senior de Emergencias Municipales de la Región de Coquimbo, Chile.
    Analiza la evidencia ingresada (Tipo: {document_type}) bajo el contexto del temporal de lluvias y vientos en Coquimbo.

    --- DATOS REGISTRADOS DE ESTA EMERGENCIA ---
    {emergency_context}

    --- ANTECEDENTES EXTRAÍDOS DE LA EVIDENCIA ---
    {file_content_text}

    Instrucciones:
    1. Si se incluye una imagen/fotografía, analiza visualmente los daños (inundación, desborde, caídas de postes/árboles, daño estructural, fallas de red eléctrica o agua potable).
    2. Clasifica el 'detected_affectation_level' en: 'Baja', 'Media', 'Alta' o 'Crítica'.
    3. Clasifica el 'detected_people_risk' en: 'Sin riesgo', 'Riesgo Bajo', 'Riesgo Medio', 'Riesgo Alto' o 'Riesgo Inminente'.
    4. NO utilices porcentajes bajo ninguna circunstancia.
    5. Extrae las alertas y metadatos con la mayor precisión operativa posible.
    6. Basa tu análisis EXCLUSIVAMENTE en los datos de esta emergencia y la evidencia adjunta. No asumas contexto externo.
    """

    content_list.append(prompt_text)

    if file_path and os.path.exists(file_path):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp"]:
            try:
                img = Image.open(file_path)
                img_byte_arr = io.BytesIO()
                img_format = img.format if img.format else "PNG"
                img.save(img_byte_arr, format=img_format)
                img_bytes = img_byte_arr.getvalue()
                
                mime_type = f"image/{img_format.lower()}"
                if mime_type == "image/jpg":
                    mime_type = "image/jpeg"

                image_part = types.Part.from_bytes(data=img_bytes, mime_type=mime_type)
                content_list.append(image_part)
            except Exception as e:
                print(f"Error procesando imagen para Gemini: {e}")

    res = client.chat.completions.create(
        model=model_name,
        response_model=DocumentSpecificAnalysis,
        messages=[{"role": "user", "content": content_list}],
        temperature=0.1
    )
    return res

def consolidate_accident_evaluation(
    previous_context: str,
    new_doc_summary: str,
    new_doc_infractions: List[Any],
    new_doc_metadata: List[Any],
    initial_affectation_level: str = "Media",
    initial_people_risk: str = "Riesgo Medio",
    previous_infractions: List[Any] = [],
    previous_metadata: List[Any] = [],
    project_data: Optional[Dict[str, Any]] = None,
    model_name: str = DEFAULT_MODEL
) -> ConsolidatedProjectEvaluation:
    """Genera la evaluación consolidada asignando las oficinas exactas de intervención.
    El contexto proviene de los datos propios de la emergencia, NO de documentos externos."""
    if not client:
        raise RuntimeError("El cliente de Gemini no está configurado. Revisa GEMINI_API_KEY.")

    # Contexto basado en los datos propios de la emergencia registrada por el usuario
    emergency_context = build_project_context(project_data)

    prompt = f"""
    Eres el Comandante Operativo de la Dirección de Gestión del Riesgo de Desastres de la Municipalidad de Coquimbo.
    Debes evaluar la emergencia y especificar exactamente CUÁLES DE LAS SIGUIENTES OFICINAS Y ESPECIALISTAS INTERVIENEN:
    - **Social**: Para damnificados, albergues, entregas de nylon/cajas de alimentos y contención social (DIDECO).
    - **Infraestructura**: Para reparación de obras municipales, contención de taludes, escombros y maquinaria pesada (Obras Municipales).
    - **Ingeniería**: Para evaluación de estabilidad vial, cortes de tránsito, señalización y diseño técnico (Tránsito / Ingeniería).
    - **Arquitectura**: Para evaluación estructural de viviendas, edificios municipales o colapsos de techumbres/muros.
    - **Especialista Hídrico**: Para colectores de aguas lluvias, roturas de matriz, evacuación de aguas con motobombas y coordinación con Aguas del Valle.
    - **Ingeniero Eléctrico**: Para postes colapsados, tableros con cortocircuito, alumbrado público desenergizado y empalmes.
    - **CGE**: Para cortes masivos de luz de media/alta tensión, cables energizados en vía pública o transformadores caídos.

    --- DATOS REGISTRADOS DE ESTA EMERGENCIA ---
    {emergency_context}

    --- CLASIFICACIÓN INICIAL DECLARADA EN REGISTRO ---
    Nivel de Afectación Inicial: {initial_affectation_level}
    Riesgo para las Personas Inicial: {initial_people_risk}

    --- CONTEXTO ACUMULADO PREVIO DE LA EMERGENCIA ---
    {previous_context}

    --- ALERTAS PREVIAS ---
    {json.dumps([dump_obj(i) for i in previous_infractions], ensure_ascii=False)}

    --- NUEVA EVIDENCIA INGRESADA ---
    Resumen del reporte/imagen: {new_doc_summary}
    Alertas detectadas: {json.dumps([dump_obj(i) for i in new_doc_infractions], ensure_ascii=False)}
    Metadatos extraídos: {json.dumps([dump_obj(m) for m in new_doc_metadata], ensure_ascii=False)}

    INSTRUCCIONES CLAVE DE EVALUACIÓN:
    1. Compara el Nivel de Afectación ({initial_affectation_level}) y Riesgo a Personas ({initial_people_risk}) iniciales con los datos REALES observados en la evidencia.
    2. Determina el 'real_affectation_level' exacto: 'Baja', 'Media', 'Alta' o 'Crítica'.
    3. Determina el 'real_people_risk' exacto: 'Sin riesgo', 'Riesgo Bajo', 'Riesgo Medio', 'Riesgo Alto' o 'Riesgo Inminente'.
    4. Suministra un 'overall_alert_level' combinado (ej: 'CRÍTICA - RIESGO INMINENTE', 'ALTA - RIESGO ALTO', 'MEDIA - RIESGO MEDIO', 'BAJA - SIN RIESGO'). JAMÁS ENTREGUES PORCENTAJES.
    5. Detalla las 'mitigation_actions' y 'action_recommendations' operativas.
    6. Identifica e incluye obligatoriamente en 'recommended_entities' todas las oficinas requeridas según el tipo de daño y necesidades (Social, Infraestructura, Ingeniería, Arquitectura, Especialista Hídrico, Ingeniero Eléctrico, CGE, Aguas del Valle).
    7. Basa tu análisis EXCLUSIVAMENTE en los datos registrados de esta emergencia y las evidencias adjuntas. No asumas contexto externo.
    """

    res = client.chat.completions.create(
        model=model_name,
        response_model=ConsolidatedProjectEvaluation,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return res