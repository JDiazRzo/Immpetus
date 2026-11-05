-- Motivo de cierre · Motivo con el que se cierra una convocatoria (POST /api/admin/vacantes/{id}/cerrar).
-- Va aparte para no tocar la 0007. Solo se llena al cerrar.
alter table vacantes add column motivo_cierre text check (char_length(motivo_cierre) <= 500);
