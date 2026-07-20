-- ----------------------------------------------------
-- CHATBOT EMERGENCIA - MIGRACIÓN RÁPIDA DE COLUMNAS
-- (EJECUTA ESTO EN EL SQL EDITOR DE SUPABASE PARA EVITAR DEADLOCKS)
-- ----------------------------------------------------

ALTER TABLE public.projects 
ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'activa',
ADD COLUMN IF NOT EXISTS project_category VARCHAR(100) DEFAULT 'Caminos y Carreteras';
