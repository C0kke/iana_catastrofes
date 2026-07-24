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
    print(f"Error inicializando el modelo: {e}")

try:
    from chatbot_emergencia_app.app.weather_service import get_extended_weather_report
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.weather_service import get_extended_weather_report
    except ModuleNotFoundError:
        from app.weather_service import get_extended_weather_report

try:
    from chatbot_emergencia_app.app.rules_engine import evaluate_emergency_rules
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.rules_engine import evaluate_emergency_rules
    except ModuleNotFoundError:
        from app.rules_engine import evaluate_emergency_rules

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INFORME_ALFA_PATH = os.path.join(BASE_DIR, "knowledge", "informe_alfa.json")
DECRETO104_PATH = os.path.join(BASE_DIR, "knowledge", "Decreto104.md")
LEY21364_PATH = os.path.join(BASE_DIR, "knowledge", "Ley21364.md")

_DECRETO104_CACHE: Optional[str] = None
_LEY21364_CACHE: Optional[str] = None

def load_decreto104_summary() -> str:
    """Carga el texto y disposiciones del Decreto Supremo N° 104 (Ley N° 16.282)."""
    global _DECRETO104_CACHE
    if _DECRETO104_CACHE:
        return _DECRETO104_CACHE

    if os.path.exists(DECRETO104_PATH):
        try:
            with open(DECRETO104_PATH, "r", encoding="utf-8") as f:
                _DECRETO104_CACHE = f.read()
                return _DECRETO104_CACHE
        except Exception as e:
            print(f"Advertencia al leer Decreto104.md: {e}")

    _DECRETO104_CACHE = """
    DECRETO SUPREMO N° 104 (LEY N° 16.282) - NORMATIVA CHILENA PARA CASOS DE SISMOS Y CATASTROFES:
    - Art. 1°: Declaración de Zonas Afectadas / Catástrofe por el Presidente de la República. Requiere sismos o catástrofes con daños de consideración masivos comprobados.
    - Art. 2°: Clasificación de Damnificados y derecho preferente a traslado, alojamiento y asistencia.
    - Art. 3°: Medidas de Excepción Administrativa y Contratación Directa de Excepción (Art. 3°b) para compras/obras de emergencia.
    - Art. 5°: Sanción de presidio a acaparamiento, venta a sobreprecio o especulación de alimentos, materiales y medicamentos en zonas afectadas.
    - Art. 6°-7°: Exención de tributos y aduanas para donaciones de ayuda nacional e internacional.
    - Art. 25°-26°: Exenciones técnicas MINVU/Municipal para demolición, reparación y reconstrucción de viviendas; supervigilancia por profesionales idóneos.
    """
    return _DECRETO104_CACHE

def load_ley21364_summary() -> str:
    """Carga las disposiciones del Sistema Nacional de Prevención y Respuesta ante Desastres (Ley N° 21.364 - SINAPRED / SENAPRED)."""
    global _LEY21364_CACHE
    if _LEY21364_CACHE:
        return _LEY21364_CACHE

    if os.path.exists(LEY21364_PATH):
        try:
            with open(LEY21364_PATH, "r", encoding="utf-8") as f:
                _LEY21364_CACHE = f.read()
                return _LEY21364_CACHE
        except Exception as e:
            print(f"Advertencia al leer Ley21364.md: {e}")

    _LEY21364_CACHE = """
    LEY N° 21.364 - SISTEMA NACIONAL DE PREVENCIÓN Y RESPUESTA ANTE DESASTRES (SINAPRED / SENAPRED):
    - Art. 2°b (Definición de Emergencia): Evento o inminencia que altera el funcionamiento de una comunidad debido a una amenaza que ocasiona afectación real o pérdidas.
      FILTRO CRÍTICO: Si NO hay amenaza inminente ni alteración comunitaria ni daños (ej. presencia preventiva de Bomberos, campamento en catastro habitual, partidos de fútbol o eventos masivos previstos), NO CONSTITUYE EMERGENCIA y NO activa los protocolos del SINAPRED ni la convocatoria a Comités COGRID.
    - Art. 2°c (Niveles de Emergencia):
      1. Emergencia Menor: Nivel comunal (gestionada con recursos municipales).
      2. Emergencia Mayor: Nivel provincial/regional (requiere apoyo del COGRID regional).
      3. Desastre: Nivel nacional (excede la capacidad regional).
      4. Catástrofe: Nivel nacional con asistencia internacional.
    - Art. 4°f (Principio de Escalabilidad): Movilización gradual y escalonada de capacidades (Comunal -> Provincial -> Regional -> Nacional).
    """
    return _LEY21364_CACHE

SEISMIC_KEYWORDS = [
    "sismo", "terremoto", "temblor", "sismico", "sísmico", "replica", "réplica",
    "epicentro", "richter", "mercalli", "decreto 104", "decreto104", "ley 16282", "ley 16.282"
]

def is_seismic_emergency(project_data: Optional[Dict[str, Any]] = None, text_content: str = "") -> bool:
    """Determina si la emergencia o la evidencia se relaciona con sismos o terremotos."""
    combined_text = text_content.lower()
    if project_data:
        combined_text += " " + str(project_data.get("name", "")).lower()
        combined_text += " " + str(project_data.get("description", "")).lower()
        combined_text += " " + str(project_data.get("project_category", "")).lower()
        combined_text += " " + str(project_data.get("observations", "")).lower()
        et = project_data.get("emergency_types", [])
        if isinstance(et, list):
            combined_text += " " + " ".join(et).lower()
        else:
            combined_text += " " + str(et).lower()

    return any(k in combined_text for k in SEISMIC_KEYWORDS)

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
    """Construye el contexto operativo a partir de los datos propios de la emergencia y el estado meteorológico (-1d a +3d)."""
    if not project_data:
        return "No hay datos de la emergencia disponibles."
    lines = []
    if project_data.get("name"):
        lines.append(f"Nombre: {project_data['name']}")
    if project_data.get("sector"):
        lines.append(f"Sector: {project_data['sector']}")
    commune = project_data.get("commune", "Coquimbo")
    lines.append(f"Comuna: {commune}")
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

    try:
        w = get_extended_weather_report(commune)
        cur = w.get("current", {})
        s4 = w.get("summary_4days", {})
        alerts = w.get("alerts", [])
        isotherm = w.get("isotherm_0_m", 2100)

        weather_lines = [
            f"Comuna: {commune}",
            f"Estado Actual: Temp {cur.get('temp_c')}°C, {cur.get('condition')}, Lluvia última hora: {cur.get('rain_last_hour_mm')} mm/h, Viento: {cur.get('wind_kmh')} km/h",
            f"Isoterma 0°C: {isotherm} m.s.n.m.",
            f"Precipitación Pasada (-24h Ayer): {s4.get('day_minus_1_rain_mm')} mm acumulados",
            f"Precipitación Proyectada Hoy (24h): {s4.get('day_0_today_rain_mm')} mm",
            f"Precipitación Proyectada +1 Día: {s4.get('day_plus_1_rain_mm')} mm",
            f"Precipitación Proyectada +2 Días: {s4.get('day_plus_2_rain_mm')} mm",
            f"Total Lluvia Proyectada 4 Días: {s4.get('total_4day_rain_mm')} mm"
        ]
        if alerts:
            alert_descs = [f"[{a.get('source')} - {a.get('severity')}] {a.get('event')}: {a.get('description')}" for a in alerts]
            weather_lines.append("ALERTAS OFICIALES DMC/ONEMI VIGENTES:")
            weather_lines.extend(alert_descs)
        else:
            weather_lines.append("Sin alertas oficiales DMC activas actualmente.")

        lines.extend(weather_lines)
    except Exception as e:
        lines.append(f"\n[Warning Clima]: No se pudo inyectar clima en tiempo real: {e}")

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
    weather_context_summary: str = Field(
        description="Resumen del escenario climático actual y proyectado a 3 días (OpenWeather/DMC) en la comuna afectada (lluvia acumulada, isoterma 0°C y alertas)."
    )
    weather_risk_impact: str = Field(
        description="Evaluación de cómo la precipitación proyectada a 72h y la cota de la isoterma agravarán el riesgo de saturación, desbordes o aluviones."
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
        description="Lista de acciones de mitigación concretas requeridas para contener la contingencia considerando la tendencia meteorológica."
    )
    action_recommendations: List[str] = Field(
        description="Recomendaciones operativas paso a paso para desplegar las cuadrillas municipales (evacuaciones preventivas, motobombas, maquinaria pesada)."
    )
    recommended_entities: List[EntityRecommendation] = Field(
        description="Lista de oficinas y profesionales especializados que deben intervenir (Social, Infraestructura, Ingeniería, Arquitectura, Especialista Hídrico, Ingeniero Eléctrico, CGE, Aguas del Valle, SENAPRED)."
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
    """Analiza un documento de texto, Word o fotografía a través de la IA.
    El contexto proviene exclusivamente de los datos de la emergencia registrada por el usuario.
    Distingue automáticamente entre evidencia fotográfica de terreno e informes oficiales (Informe Alfa, fichas, etc.)."""
    if not genai_client:
        raise RuntimeError("El cliente de análisis no está configurado. Revisa la clave")

    emergency_context = build_project_context(project_data)

    # Detectar si hay imagen adjunta
    has_image = False
    image_part = None
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
                has_image = True
            except Exception as e:
                print(f"Error procesando imagen: {e}")

    # Esquema JSON esperado para la respuesta estructurada
    json_schema = '''{
  "document_summary": "string (resumen conciso, máx 300 palabras)",
  "is_valid_architectural_doc": true/false,
  "detected_affectation_level": "'Baja' | 'Media' | 'Alta' | 'Crítica'",
  "detected_people_risk": "'Sin riesgo' | 'Riesgo Bajo' | 'Riesgo Medio' | 'Riesgo Alto' | 'Riesgo Inminente'",
  "infractions": [{"rule_id": "string", "description": "string", "severity": "'CRÍTICA'|'ALTA'|'MEDIA'|'BAJA'", "evidence": "string", "justification": "string"}],
  "extracted_metadata": [{"key": "string", "value": "string"}]
}'''

    # Cargar Marco Legal (Ley N° 21.364 SINAPRED y Decreto N° 104)
    ley21364_text = load_ley21364_summary()
    seismic_active = is_seismic_emergency(project_data, file_content_text)
    
    legal_section = f"""
--- MARCO LEGAL CHILENO OBLIGATORIO: LEY N° 21.364 (SINAPRED / SENAPRED) ---
{ley21364_text}

INSTRUCCIÓN DE FILTRADO Y VALIDACIÓN DE EVENTO (LEY 21.364):
1. Contrasta si el evento constituye una EMERGENCIA REAL según el Art. 2b de la Ley 21.364.
2. Si el registro o archivo corresponde a una ACTIVIDAD REGULAR / NO EMERGENTE (ej. partido de fútbol, desfile, evento masivo regulado, presencia o llegada preventiva de Bomberos sin siniestro, campamento en catastro habitual sin siniestro):
   - Clasifica obligatoriamente 'detected_affectation_level' = 'Baja' y 'detected_people_risk' = 'Sin riesgo'.
   - En 'document_summary' indica explícitamente que la situación es un evento regular o preventivo y NO activa los protocolos del SINAPRED ni COGRID.
"""

    if seismic_active:
        decreto_text = load_decreto104_summary()
        legal_section += f"""
--- CONOCIMIENTO Y EVALUACIÓN SÍSMICA CRÍTICA: DECRETO SUPREMO N° 104 (LEY N° 16.282) ---
{decreto_text}

CRITERIO RÍGIDO SOBRE SISMOS / TERREMOTOS:
- NO solicites ni sugieras declarar "Zona de Catástrofe" (Decreto 104) si la magnitud del sismo es desconocida (ej. puede tratarse de un temblor menor de 3.2 MW) o si no hay antecedentes de colapsos estructurales graves.
- Si no hay certeza de alta magnitud o de destrucción masiva, en las recomendaciones DEBES REQUERIR:
  1) Informe oficial del Centro Sismológico Nacional (CSN) con magnitud y epicentro exacto.
  2) Despliegue inmediato de inspección técnica estructural EDAN / Dirección de Obras Municipales (DOM) en terreno para evaluar si existen daños reales antes de cualquier escalamiento.
- Solo si se confirma magnitud elevada (>= 6.5) o destrucción estructural masiva, se justifica recomendar la activación de Zona de Catástrofe.
"""

    prompt_text = f"""Eres un Evaluador Senior de Emergencias Municipales de la Región de Coquimbo, Chile.
Analiza la evidencia ingresada (Tipo declarado: {document_type}) bajo el contexto operativo de la emergencia.
{legal_section}
--- DATOS REGISTRADOS DE ESTA EMERGENCIA ---
{emergency_context}

--- ANTECEDENTES EXTRAÍDOS DE LA EVIDENCIA ---
{file_content_text}

INSTRUCCIONES DE CLASIFICACIÓN DEL DOCUMENTO:
Primero, determina la NATURALEZA del archivo adjunto:
A) **Evidencia Fotográfica de Terreno**: Fotografías tomadas en campo que muestran daños visibles (inundación, desborde, socavón, caída de postes/árboles, daño estructural, fallas de red eléctrica o agua potable). Para estas, analiza visualmente cada daño observable.
B) **Informe Oficial / Documento Técnico**: Documentos como Informe Alfa, fichas EDAN, reportes SENAPRED, partes policiales, fichas SAMU o informes Word. Para estos, extrae datos estadísticos clave (personas afectadas, viviendas dañadas, recursos desplegados, necesidades evaluadas) y clasifícalos como metadatos estructurados.
C) **Fotografía de Documento/Informe**: Si la imagen es una CAPTURA o FOTO de un documento impreso (Informe Alfa, formulario, tabla), NO analices daños visuales; en su lugar lee y extrae todo el texto y datos del documento fotografiado (cifras, fechas, clasificaciones, recursos solicitados).

INSTRUCCIONES DE ANÁLISIS:
1. Clasifica el 'detected_affectation_level' en: 'Baja', 'Media', 'Alta' o 'Crítica'.
2. Clasifica el 'detected_people_risk' en: 'Sin riesgo', 'Riesgo Bajo', 'Riesgo Medio', 'Riesgo Alto' o 'Riesgo Inminente'.
3. NO utilices porcentajes bajo ninguna circunstancia.
4. Extrae las alertas y metadatos con la mayor precisión operativa posible.
5. Basa tu análisis EXCLUSIVAMENTE en los datos de esta emergencia y la evidencia adjunta.
6. En el 'document_summary', indica explícitamente si el documento es evidencia fotográfica de terreno, un informe oficial, o una foto de documento.

Responde ÚNICAMENTE con un JSON válido con este esquema (sin bloques de código markdown):
{json_schema}"""

    # Construir contenido multimodal para genai nativo
    content_parts = [prompt_text]
    if has_image and image_part:
        content_parts.append(image_part)

    # Usar el cliente genai nativo directamente (soporta types.Part para imágenes)
    response = genai_client.models.generate_content(
        model=model_name,
        contents=content_parts,
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json"
        )
    )

    # Parsear la respuesta JSON a nuestro modelo Pydantic
    raw_text = response.text.strip()
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        # Intentar extraer JSON de bloques de código markdown
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_text)
        if json_match:
            parsed = json.loads(json_match.group(1))
        else:
            raise ValueError(f"No se pudo parsear la respuesta de IA como JSON: {raw_text[:500]}")

    return DocumentSpecificAnalysis(**parsed)

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
        raise RuntimeError("El cliente de análisis no está configurado. Revisa la clave")

    emergency_context = build_project_context(project_data)

    ley21364_text = load_ley21364_summary()
    seismic_active = is_seismic_emergency(project_data, new_doc_summary + " " + previous_context)
    
    legal_section = f"""
    --- MARCO LEGAL VIGENTE: LEY N° 21.364 (SINAPRED / SENAPRED) ---
    {ley21364_text}

    EVALUACIÓN DE ESTADO DEL EVENTO (LEY 21.364):
    - Contrasta si la situación constituye o no una emergencia real. Si se trata de un evento deportivo (partido de fútbol), desfile, llegada/patrullaje preventivo de Bomberos sin siniestro, o campamento en catastro de rutina sin siniestro:
      * Suministra 'real_affectation_level' = 'Baja', 'real_people_risk' = 'Sin riesgo' y 'overall_alert_level' = 'BAJA - SIN RIESGO'.
      * En las recomendaciones aclara explícitamente que NO corresponde activar Comités COGRID ni los protocolos de emergencia del SINAPRED.
"""

    if seismic_active:
        decreto_text = load_decreto104_summary()
        legal_section += f"""
    --- EVALUACIÓN CRÍTICA DE SISMOS Y TERREMOTOS (DECRETO SUPREMO N° 104 & LEY 21.364) ---
    {decreto_text}

    INSTRUCCIONES RÍGIDAS SOBRE SISMOS / TERREMOTOS:
    - Evalúa la magnitud informada. Si la magnitud es DESCONOCIDA (ej. puede tratarse de un temblor menor de 3.2 MW) o no hay antecedentes constatados de colapsos estructurales graves:
      * ESTÁ ESTRICTAMENTE PROHIBIDO solicitar o recomendar "Zona de Catástrofe" bajo el Decreto 104.
      * En 'mitigation_actions' y 'action_recommendations', DEBES REQUERIR OBLIGATORIAMENTE:
        1) Confirmación e informe oficial al Centro Sismológico Nacional (CSN) de la magnitud y profundidad.
        2) Catastro de terreno de emergencia (EDAN) y evaluación estructural por la Dirección de Obras Municipales (DOM) para verificar daños reales.
    - Únicamente si se confirma una magnitud elevada (>= 6.5) o destrucción masiva comprobada, se justificará evaluar solicitar Zona de Catástrofe (Decreto 104) y COGRID Regional/Nacional (Ley 21.364).
"""

    prompt = f"""
    Eres el Comandante Operativo de la Dirección de Gestión del Riesgo de Desastres de la Municipalidad de Coquimbo.
    {legal_section}
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