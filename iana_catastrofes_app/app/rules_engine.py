import re
from typing import List, Dict, Any

def evaluate_emergency_rules(text: str, project_type: str) -> List[Dict[str, Any]]:
    """Evalúa reglas automáticas de detección inmediata sobre informes de accidentes en ruta."""
    alerts = []
    text_lower = text.lower()

    # Detección de sustancias peligrosas (HazMat)
    if any(k in text_lower for k in ["hazmat", "combust", "quimic", "cisterna", "derrame", "inflamable", "acido", "gas"]):
        alerts.append({
            "rule_id": "HazMat Protocol Article 2",
            "description": "Presencia detectada o riesgo inminente de derrame de Sustancias Peligrosas.",
            "severity": "ALTA",
            "evidence": "Términos relacionados con químicos/combustibles en el informe",
            "justification": "Exige perímetro de aislamiento inmediato de 300 a 800 metros y notificación a unidades HazMat."
        })

    # Detección de víctimas críticas o atrapadas
    if any(k in text_lower for k in ["atrapad", "fallecid", "vital", "triage rojo", "grave", "muerto"]):
        alerts.append({
            "rule_id": "ABC Protocol Triage START",
            "description": "Se registran víctimas atrapadas o en estado crítico (Código Rojo/Negro).",
            "severity": "ALTA",
            "evidence": "Mención de atrapados o lesionados de gravedad en el texto",
            "justification": "Requiere despacho de helitransporte y rescate vehicular pesado."
        })

    # Detección de corte total de carretera / infraestructura
    if any(k in text_lower for k in ["corte total", "bloqueo", "ambas pistas", "colapso", "puente"]):
        alerts.append({
            "rule_id": "MOP Vialidad Article 3",
            "description": "Interrupción total de la ruta o colapso de infraestructura vial.",
            "severity": "ALTA",
            "evidence": "Cierre completo de pistas registrado",
            "justification": "Exige habilitación de desvíos de emergencia y notificación a SENAPRED."
        })

    return alerts