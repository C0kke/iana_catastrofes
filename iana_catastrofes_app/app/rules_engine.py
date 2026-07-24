import re
from typing import List, Dict, Any

def evaluate_emergency_rules(text: str, project_type: str) -> List[Dict[str, Any]]:
    """Evalúa reglas automáticas sobre reportes bajo el marco de la Ley N° 21.364 (SINAPRED) y Decreto N° 104."""
    alerts = []
    text_lower = text.lower()

    # Detección de Eventos No Emergentes (Ley N° 21.364 Art. 2b)
    # Eventos como partidos de fútbol, campamentos en catastro regular, actividades preventivas o patrullajes no constituyen emergencia.
    is_routine_event = any(k in text_lower for k in [
        "partido de futbol", "partido de fútbol", "estadio", "desfile", "actividad comunitaria", 
        "campamento regular", "catastro campamento", "inspeccion de rutina", "inspección de rutina", "patrullaje preventivo"
    ])
    has_real_damage = any(k in text_lower for k in [
        "colapso", "herido", "atrapado", "fallecido", "inundac", "incendio", "derrame", "destruid", "bloqueo", "evacuac", "emergencia"
    ])

    if is_routine_event and not has_real_damage:
        alerts.append({
            "rule_id": "Ley N° 21.364 Art. 2b - Evento Regular / Sin Emergencia",
            "description": "Actividad regular, preventiva o de catastro que no constituye emergencia según Ley 21.364.",
            "severity": "BAJA",
            "evidence": "Registro de actividad rutinaria o preventiva sin amenaza ni daños inmediatos",
            "justification": "No activa los protocolos del Sistema Nacional de Prevención y Respuesta ante Desastres (SINAPRED) ni requiere convocatoria a Comités COGRID."
        })
        return alerts

    # Detección y Evaluación Rigurosa de Sismos / Terremotos (Decreto Supremo 104 / Ley 16.282)
    if any(k in text_lower for k in ["sismo", "terremoto", "temblor", "sismico", "sísmico", "replica", "réplica", "epicentro", "richter", "mercalli", "decreto 104", "ley 16282", "ley 16.282"]):
        # Extraer posible magnitud en texto (ej. "magnitud 6.8", "6.8 richter", "Mw 7.2", "3.2")
        mag_match = re.search(r'(?:magnitud|mw|richter|escala)?\s*([1-9]\.[0-9])', text_lower)
        mag_val = float(mag_match.group(1)) if mag_match else None

        # Si hay daños estructurales masivos o magnitud alta (>= 6.5)
        has_catastrophic_damage = any(k in text_lower for k in ["colapso masivo", "destruccion total", "tsunami", "catastrofe", "catástrofe", "muertos masivos", "derrumbe de edificios"])
        
        if (mag_val and mag_val >= 6.5) or has_catastrophic_damage:
            alerts.append({
                "rule_id": "Decreto Supremo 104 / Ley 16.282 - Catástrofe Sísmica",
                "description": f"Terremoto de alta intensidad detectado{' (Magnitud ' + str(mag_val) + ')' if mag_val else ''} con severo impacto.",
                "severity": "CRÍTICA",
                "evidence": "Sismo de alta magnitud o daños estructurales severos constatados",
                "justification": "Procede la solicitud de Declaración de Zona de Catástrofe (Art. 1°), Contratación Directa de Excepción (Art. 3°b), Exenciones Técnicas MINVU para reconstrucción (Art. 25°-26°) y activación del COGRID Nacional/Regional (Ley 21.364)."
            })
        else:
            # Sismo con magnitud desconocida o menor (< 6.5): PROHIBIDO solicitar Zona de Catástrofe directamente
            mag_str = f"Magnitud detectada/estimada: {mag_val}" if mag_val else "Magnitud exacta NO informada en el reporte (ej. posible evento menor < 5.0 o 3.2)"
            alerts.append({
                "rule_id": "Ley 21.364 / Verificación Sísmica CSN (Sin Zona de Catástrofe)",
                "description": f"Sismo registrado pero sin confirmación de alta intensidad. {mag_str}.",
                "severity": "MEDIA",
                "evidence": "Reporte de sismo o temblor sin verificación de magnitud sísmica ni destrucción comprobada",
                "justification": "NO procede solicitar Zona de Catástrofe (Decreto 104) sin confirmación de magnitud superior a 6.5 o destrucción comprobada. Se DEBE requerir datos oficiales del Centro Sismológico Nacional (CSN) y desplegar catastro de terreno EDAN/DOM antes de cualquier escalamiento."
            })

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