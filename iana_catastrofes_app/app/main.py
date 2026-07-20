import os
import uuid
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

try:
    from chatbot_emergencia_app.app.version import __version__
    from chatbot_emergencia_app.app.pdf_extract import extract_text_from_file
    from chatbot_emergencia_app.app.rules_engine import evaluate_emergency_rules
    from chatbot_emergencia_app.app.ai_verifier import analyze_single_document, consolidate_accident_evaluation
    from chatbot_emergencia_app.app.db import (
        get_project_by_id,
        update_project_evaluation,
        add_document_to_project,
        add_document_analysis
    )
except ModuleNotFoundError:
    try:
        from iana_catastrofes_app.app.version import __version__
        from iana_catastrofes_app.app.pdf_extract import extract_text_from_file
        from iana_catastrofes_app.app.rules_engine import evaluate_emergency_rules
        from iana_catastrofes_app.app.ai_verifier import analyze_single_document, consolidate_accident_evaluation
        from iana_catastrofes_app.app.db import (
            get_project_by_id,
            update_project_evaluation,
            add_document_to_project,
            add_document_analysis
        )
    except ModuleNotFoundError:
        from app.version import __version__
        from app.pdf_extract import extract_text_from_file
        from app.rules_engine import evaluate_emergency_rules
        from app.ai_verifier import analyze_single_document, consolidate_accident_evaluation
        from app.db import (
            get_project_by_id,
            update_project_evaluation,
            add_document_to_project,
            add_document_analysis
        )

app = FastAPI(
    title=f"Emergencias Coquimbo v{__version__}",
    description="API de Análisis en Tiempo Real para Emergencias"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
RESULTS_DIR = os.path.join(DATA_DIR, "results")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": __version__, "service": "Chatbot Emergencia API"}

@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    document_type: str = Form("police_report")
):
    """Sube y analiza un documento o evidencia de emergencia."""
    job_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(UPLOADS_DIR, f"{job_id}{file_ext}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        
    extracted_text = extract_text_from_file(file_path)

    # Obtener datos del proyecto para usarlos como contexto de IA
    proj = get_project_by_id(project_id) if project_id else None

    # Reglas automáticas rápidas
    quick_rules = evaluate_emergency_rules(extracted_text, document_type)
    
    # Análisis IA (contexto basado en datos de la emergencia)
    ai_doc_result = analyze_single_document(extracted_text, document_type, file_path=file_path, project_data=proj)
    
    # Combinar alertas
    all_infractions = quick_rules + [i.model_dump() for i in ai_doc_result.infractions]
    
    res_data = {
        "job_id": job_id,
        "file_name": file.filename,
        "document_summary": ai_doc_result.document_summary,
        "is_valid_emergency_doc": ai_doc_result.is_valid_architectural_doc,
        "infractions": all_infractions,
        "extracted_metadata": [m.model_dump() for m in ai_doc_result.extracted_metadata]
    }
    
    # Guardar en JSON local
    res_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    with open(res_path, "w", encoding="utf-8") as f:
        json.dump(res_data, f, ensure_ascii=False, indent=2)
        
    # Actualizar emergencia en Supabase si project_id está presente
    if project_id and proj:
        doc_rec = add_document_to_project(project_id, file.filename, document_type, file_path)
        if doc_rec.get("id"):
            add_document_analysis(doc_rec["id"], ai_doc_result.document_summary, all_infractions, [m.model_dump() for m in ai_doc_result.extracted_metadata])
            
        prev_context = proj.get("consolidated_context", "")
        prev_infractions = proj.get("consolidated_infractions", [])
        prev_meta = proj.get("extracted_metadata", [])
        
        eval_res = consolidate_accident_evaluation(
            previous_context=prev_context,
            new_doc_summary=ai_doc_result.document_summary,
            new_doc_infractions=ai_doc_result.infractions,
            new_doc_metadata=ai_doc_result.extracted_metadata,
            project_data=proj
        )
        
        update_project_evaluation(
            project_id=project_id,
            consolidated_context=eval_res.consolidated_context,
            consolidated_infractions=[i.model_dump() for i in eval_res.consolidated_infractions],
            success_probability=eval_res.success_probability,
            extracted_metadata=[m.model_dump() for m in eval_res.extracted_metadata]
        )
            
    return JSONResponse(content=res_data)

@app.get("/api/result/{job_id}")
def get_result(job_id: str):
    res_path = os.path.join(RESULTS_DIR, f"{job_id}.json")
    if not os.path.exists(res_path):
        raise HTTPException(status_code=404, detail="Resultado no encontrado.")
    with open(res_path, "r", encoding="utf-8") as f:
        return json.load(f)