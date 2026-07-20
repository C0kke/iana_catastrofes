-- ----------------------------------------------------
-- CHATBOT EMERGENCIA - REGIÓN DE COQUIMBO
-- ESQUEMA DE BASE DE DATOS SUPABASE (ACCESO ABIERTO CON RLS PERMISIVO)
-- ----------------------------------------------------
-- Proyecto Supabase: https://vdqeadbppejgstqfobpl.supabase.co
-- ----------------------------------------------------

DROP TABLE IF EXISTS public.document_analyses CASCADE;
DROP TABLE IF EXISTS public.documents CASCADE;
DROP TABLE IF EXISTS public.projects CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

DO $$ 
BEGIN
    DROP TYPE IF EXISTS public.document_type CASCADE;
    DROP TYPE IF EXISTS public.project_type CASCADE;
    
    CREATE TYPE public.project_type AS ENUM (
        'inundacion',
        'anegamiento',
        'remocion_masa',
        'derrumbe',
        'socavon',
        'caida_arbol',
        'caida_poste',
        'dano_estructural',
        'rotura_matriz',
        'dano_pavimento',
        'dano_vereda',
        'dano_plaza',
        'dano_alumbrado',
        'emergencia_costera',
        'other'
    );

    CREATE TYPE public.document_type AS ENUM (
        'police_report',
        'medical_triage_log',
        'site_photo',
        'word_report',
        'witness_statement',
        'hazmat_sheet',
        'other'
    );
END $$;

CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    shift_number VARCHAR(50) DEFAULT '1',
    chile_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    address VARCHAR(255),
    sector VARCHAR(100),
    project_category VARCHAR(100) DEFAULT 'Caminos y Carreteras',
    project_type public.project_type NOT NULL DEFAULT 'other',
    emergency_types JSONB DEFAULT '[]'::jsonb,
    description TEXT,
    affectation_level VARCHAR(50),
    people_risk VARCHAR(50),
    affectations JSONB DEFAULT '[]'::jsonb,
    requirements_list JSONB DEFAULT '[]'::jsonb,
    attention_priority VARCHAR(50),
    observations TEXT,
    follow_up BOOLEAN DEFAULT FALSE,
    follow_up_responsible VARCHAR(255),
    
    region VARCHAR(100) NOT NULL DEFAULT 'Coquimbo',
    commune VARCHAR(100) NOT NULL DEFAULT 'La Serena',
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    status VARCHAR(50) DEFAULT 'activa',
    
    overall_alert_level VARCHAR(50) DEFAULT 'MEDIO',
    real_affectation_level VARCHAR(50) DEFAULT 'Media',
    real_people_risk VARCHAR(50) DEFAULT 'Riesgo Medio',
    initial_vs_real_risk_evaluation TEXT,
    mitigation_actions JSONB DEFAULT '[]'::jsonb,
    action_recommendations JSONB DEFAULT '[]'::jsonb,
    recommended_entities JSONB DEFAULT '[]'::jsonb,
    
    consolidated_context TEXT DEFAULT 'Emergencia registrada. Pendiente de recepción de evidencias y reportes de terreno.',
    consolidated_infractions JSONB DEFAULT '[]'::jsonb, 
    extracted_metadata JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: documents
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    document_type public.document_type NOT NULL,
    bucket_path VARCHAR(512) NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla: document_analyses
CREATE TABLE IF NOT EXISTS public.document_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    extracted_text_summary TEXT NOT NULL,
    infractions JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_project_id ON public.documents(project_id);
CREATE INDEX IF NOT EXISTS idx_analyses_document_id ON public.document_analyses(document_id);

-- HABILITAR RLS CON POLÍTICAS PERMISIVAS
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_analyses ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public full access to projects" ON public.projects;
CREATE POLICY "Public full access to projects" ON public.projects FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access to documents" ON public.documents;
CREATE POLICY "Public full access to documents" ON public.documents FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Public full access to document_analyses" ON public.document_analyses;
CREATE POLICY "Public full access to document_analyses" ON public.document_analyses FOR ALL USING (true) WITH CHECK (true);

-- Tabla: critical_points (Puntos Críticos / Rutas Cortadas)
CREATE TABLE IF NOT EXISTS public.critical_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    commune VARCHAR(100) NOT NULL DEFAULT 'Coquimbo',
    sector VARCHAR(100),
    address VARCHAR(255),
    point_type VARCHAR(100) DEFAULT 'ruta_cortada',
    severity VARCHAR(50) DEFAULT 'CRÍTICO',
    status VARCHAR(50) DEFAULT 'activo',
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_critical_points_commune ON public.critical_points(commune);
ALTER TABLE public.critical_points ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Public full access to critical_points" ON public.critical_points;
CREATE POLICY "Public full access to critical_points" ON public.critical_points FOR ALL USING (true) WITH CHECK (true);