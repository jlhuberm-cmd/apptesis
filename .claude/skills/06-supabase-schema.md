# 06 · Esquema Supabase

Tablas: `users`, `verification_codes`, `survey_responses` (PostgreSQL 15+).
DDL en `infrastructure/database/migrations/001_initial_schema.sql`.
Índices en email, user_id, upload_batch_id y scores. RLS básico.
