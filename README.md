# IANA - EMERGENCIA

Sistema inteligente de gestión, análisis en tiempo real y soporte para la toma de decisiones ante desastres climáticos y eventos de emergencia a nivel municipal en la **Región de Coquimbo, Chile**.

---

## Contexto y Propósito

Ante frentes de mal tiempo de gran magnitud, temporales, anegamientos masivos, socavones, desbordes, desprendimientos en rutas interurbanas y aislamiento de comunidades, los equipos municipales de gestión del riesgo necesitan procesar volúmenes elevados de solicitudes y evidencia de campo para **priorizar recursos y asignar cuadrillas de respuesta rápida**.

**IANA - EMERGENCIA** actúa como un Centro de Mando Digital que:
- **Centraliza las solicitudes de emergencia municipal:** Registra dirección, sector, tipo de evento (inundación, socavón, caída de postes/árboles, daño estructural, aislamiento), nivel de afectación y riesgo directo para las personas.
- **Procesa evidencia multimodal de terreno:** Analiza fotografías tomadas en el lugar, informes técnicos en Word (.docx) y partes/fichas en PDF utilizando Inteligencia Artificial (**Gemini Multimodal Vision**).
- **Establece criterios y entregables operativos:** Evalúa automáticamente el grado de mitigación de la escena (0-100%), identifica riesgos desbordados e integra recomendaciones operativas claras para coordinar cuadrillas de maquinaria pesada (retroexcavadoras, camiones aljibe, tolva) y equipos de emergencia en terreno.

---

## Estructura del Sistema

- **Frontend:** Streamlit (Centro de Mando Operativo en modo oscuro de alto contraste)
- **Backend Operativo:** FastAPI + Instructor + Google Gemini API (`gemini-3.1-flash-lite` / `gemini-2.5-flash`)
- **Procesamiento de Evidencia:** `PyMuPDF` (PDF), `python-docx` (Informes Word) y `Pillow` (Fotografías JPG/PNG/WEBP)
- **Base de Datos Relacional:** Supabase PostgreSQL (`supabase_schema.sql`)

---

## Guía de Inicio Rápido

### 1. Clonar e Instalar Dependencias

```powershell
# Crear el entorno virtual de Python
python -m venv .venv

# Activar el entorno virtual (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Instalar los paquetes requeridos
pip install -r requirements.txt
```

### 2. Configurar la Base de Datos Supabase

1. Accede a tu panel en [Supabase](https://supabase.com).
2. Abre el **SQL Editor** en tu proyecto.
3. Copia y ejecuta el contenido del archivo [`supabase_schema.sql`](file:///C:/Users/cokey/Documents/Programacion/iana_catastrofes/supabase_schema.sql).
4. Verifica que el archivo `.env` contenga tu `GEMINI_API_KEY` y las credenciales `SUPABASE_URL` y `SUPABASE_PUBLISHABLE_KEY`.

### 3. Iniciar el Centro de Mando (Streamlit)

Ejecuta el siguiente comando desde la raíz del proyecto:

```powershell
streamlit run .\iana_catastrofes_app\streamlit_app.py
```

La aplicación se abrirá automáticamente en tu navegador web en `http://localhost:8501`.

---

## Flujo de Trabajo en Emergencia

1. **Ingreso al Centro de Mando:** Define el **Turno Activo** en la pantalla principal (la hora oficial de Chile se sincroniza de forma automática).
2. **Registro de la Emergencia:** Presiona **+ Registrar Nueva Emergencia** e ingresa la dirección, sector y tipo de afectación en terreno.
3. **Carga de Evidencia Fotográfica y Reportes:** Sube fotografías tomadas por inspectores o vecinos, o documentos Word/PDF de las cuadrillas.
4. **Determinación y Criterio de Respuesta:** Revisa el nivel de control acumulado y las alertas prioritarias para despachar maquinaria y recursos municipales.