import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

try:
    from zoneinfo import ZoneInfo
    CHILE_TZ = ZoneInfo("America/Santiago")
except Exception:
    from datetime import timezone, timedelta
    CHILE_TZ = timezone(timedelta(hours=-4))

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")

try:
    from supabase import create_client, Client
    supabase_client: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY) if SUPABASE_URL and SUPABASE_SECRET_KEY else None
except Exception as e:
    print(f"Advertencia: No se pudo conectar a Supabase: {e}")
    supabase_client = None

def get_chile_now_iso() -> str:
    """Retorna la hora actual en Chile en formato ISO 8601."""
    return datetime.now(CHILE_TZ).isoformat()

def create_project(
    name: str,
    shift_number: str = "1",
    chile_time: str = "",
    address: str = "",
    sector: str = "",
    project_category: str = "Caminos y Carreteras",
    project_type: str = "other",
    emergency_types: List[str] = [],
    description: str = "",
    affectation_level: str = "Media",
    people_risk: str = "Riesgo Medio",
    affectations: List[str] = [],
    requirements_list: List[str] = [],
    attention_priority: str = "DENTRO DEL DIA",
    observations: str = "",
    follow_up: bool = False,
    follow_up_responsible: str = "",
    region: str = "Coquimbo",
    commune: str = "La Serena",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    status: str = "activa"
) -> Dict[str, Any]:
    """Crea un nuevo registro de Emergencia en la Región de Coquimbo."""
    if not chile_time:
        chile_time = get_chile_now_iso()

    data = {
        "name": name,
        "shift_number": shift_number,
        "chile_time": chile_time,
        "address": address,
        "sector": sector,
        "project_category": project_category,
        "project_type": project_type if project_type else "other",
        "emergency_types": emergency_types,
        "description": description,
        "affectation_level": affectation_level,
        "people_risk": people_risk,
        "affectations": affectations,
        "requirements_list": requirements_list,
        "attention_priority": attention_priority,
        "observations": observations,
        "follow_up": follow_up,
        "follow_up_responsible": follow_up_responsible,
        "region": region,
        "commune": commune,
        "latitude": latitude,
        "longitude": longitude,
        "status": status,
        "real_affectation_level": affectation_level,
        "real_people_risk": people_risk,
        "overall_alert_level": f"{affectation_level.upper()} - {people_risk.upper()}",
        "initial_vs_real_risk_evaluation": "Pendiente de evaluación de terreno frente al frente de mal tiempo.",
        "mitigation_actions": [],
        "action_recommendations": [],
        "recommended_entities": [],
        "consolidated_context": "Emergencia registrada. Pendiente de recepción de evidencias y reportes de terreno.",
        "consolidated_infractions": [],
        "extracted_metadata": {}
    }
    
    if not supabase_client:
        data["id"] = f"local-{int(datetime.now().timestamp())}"
        data["created_at"] = chile_time
        return data

    try:
        res = supabase_client.table("projects").insert(data).execute()
        return res.data[0] if res.data else data
    except Exception as e:
        print(f"Advertencia al guardar en Supabase (usando respaldo local): {e}")
        data["id"] = f"local-{int(datetime.now().timestamp())}"
        data["created_at"] = chile_time
        return data

def update_project_details(
    project_id: str,
    name: str,
    shift_number: str,
    address: str,
    sector: str,
    project_category: str,
    emergency_types: List[str],
    description: str,
    affectation_level: str,
    people_risk: str,
    affectations: List[str],
    requirements_list: List[str],
    attention_priority: str,
    observations: str,
    follow_up: bool,
    follow_up_responsible: str,
    region: str,
    commune: str,
    latitude: Optional[float],
    longitude: Optional[float]
) -> Dict[str, Any]:
    """Edita y actualiza los datos principales de una emergencia existente."""
    if not supabase_client or project_id.startswith("local-"):
        return {}
    data = {
        "name": name,
        "shift_number": shift_number,
        "address": address,
        "sector": sector,
        "project_category": project_category,
        "emergency_types": emergency_types,
        "description": description,
        "affectation_level": affectation_level,
        "people_risk": people_risk,
        "affectations": affectations,
        "requirements_list": requirements_list,
        "attention_priority": attention_priority,
        "observations": observations,
        "follow_up": follow_up,
        "follow_up_responsible": follow_up_responsible,
        "region": region,
        "commune": commune,
        "latitude": latitude,
        "longitude": longitude
    }
    try:
        res = supabase_client.table("projects").update(data).eq("id", project_id).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        print(f"Advertencia al actualizar datos de la emergencia en Supabase: {e}")
        return {}

def list_projects(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene la lista de emergencias registradas opcionalmente filtradas por estado."""
    if not supabase_client:
        return []
    try:
        res = supabase_client.table("projects").select("*").order("created_at", desc=True).execute()
        items = res.data or []
        if status_filter:
            return [i for i in items if i.get("status", "activa") == status_filter]
        return items
    except Exception as e:
        print(f"Advertencia al consultar Supabase: {e}")
        return []

def get_project_by_id(project_id: str) -> Optional[Dict[str, Any]]:
    """Obtiene el detalle de una emergencia por ID."""
    if not supabase_client or project_id.startswith("local-"):
        return None
    try:
        res = supabase_client.table("projects").select("*").eq("id", project_id).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"Advertencia al obtener proyecto de Supabase: {e}")
        return None

def update_project_status(project_id: str, new_status: str) -> Dict[str, Any]:
    """Actualiza el estado de la emergencia ('activa', 'tratada', 'solucionada')."""
    if not supabase_client or project_id.startswith("local-"):
        return {}
    try:
        res = supabase_client.table("projects").update({"status": new_status}).eq("id", project_id).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        print(f"Advertencia al actualizar estado en Supabase: {e}")
        return {}

def update_project_evaluation(
    project_id: str,
    consolidated_context: str,
    initial_vs_real_risk_evaluation: str,
    real_affectation_level: str,
    real_people_risk: str,
    overall_alert_level: str,
    mitigation_actions: List[str],
    action_recommendations: List[str],
    recommended_entities: List[Dict[str, Any]],
    consolidated_infractions: List[Dict[str, Any]],
    extracted_metadata: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Actualiza la evaluación acumulada de control de la emergencia (Sin porcentajes)."""
    if not supabase_client or project_id.startswith("local-"):
        return {}
    
    data = {
        "consolidated_context": consolidated_context,
        "initial_vs_real_risk_evaluation": initial_vs_real_risk_evaluation,
        "real_affectation_level": real_affectation_level,
        "real_people_risk": real_people_risk,
        "overall_alert_level": overall_alert_level,
        "mitigation_actions": mitigation_actions,
        "action_recommendations": action_recommendations,
        "recommended_entities": recommended_entities,
        "consolidated_infractions": consolidated_infractions,
        "extracted_metadata": extracted_metadata
    }
    try:
        res = supabase_client.table("projects").update(data).eq("id", project_id).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        print(f"Advertencia al actualizar evaluación en Supabase: {e}")
        return {}

def update_project_coordinates(
    project_id: str,
    latitude: float,
    longitude: float
) -> Dict[str, Any]:
    """Actualiza las coordenadas georreferenciadas de la emergencia."""
    if not supabase_client or project_id.startswith("local-"):
        return {}
    data = {
        "latitude": latitude,
        "longitude": longitude
    }
    try:
        res = supabase_client.table("projects").update(data).eq("id", project_id).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        print(f"Advertencia al actualizar coordenadas en Supabase: {e}")
        return {}

def add_document_to_project(
    project_id: str,
    file_name: str,
    document_type: str,
    bucket_path: str
) -> Dict[str, Any]:
    """Registra una nueva evidencia (PDF, Word, Imagen) en la base de datos."""
    if not supabase_client or project_id.startswith("local-"):
        return {"id": f"doc-local-{int(datetime.now().timestamp())}", "file_name": file_name}
    data = {
        "project_id": project_id,
        "file_name": file_name,
        "document_type": document_type,
        "bucket_path": bucket_path
    }
    try:
        res = supabase_client.table("documents").insert(data).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        print(f"Advertencia al agregar documento en Supabase: {e}")
        return {"id": f"doc-local-{int(datetime.now().timestamp())}", "file_name": file_name}

def list_project_documents(project_id: str) -> List[Dict[str, Any]]:
    """Lista todas las evidencias cargadas para una emergencia."""
    if not supabase_client or project_id.startswith("local-"):
        return []
    try:
        res = supabase_client.table("documents").select("*").eq("project_id", project_id).order("uploaded_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        print(f"Advertencia al listar documentos en Supabase: {e}")
        return []

def add_document_analysis(
    document_id: str,
    summary: str,
    infractions: List[Dict[str, Any]],
    metadata: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Guarda el análisis de la evidencia en la base de datos."""
    if not supabase_client or document_id.startswith("doc-local-"):
        return {}
    data = {
        "document_id": document_id,
        "extracted_text_summary": summary,
        "infractions": infractions,
        "metadata": metadata
    }
    try:
        res = supabase_client.table("document_analyses").insert(data).execute()
        return res.data[0] if res.data else {}
    except Exception as e:
        print(f"Advertencia al agregar análisis en Supabase: {e}")
        return {}