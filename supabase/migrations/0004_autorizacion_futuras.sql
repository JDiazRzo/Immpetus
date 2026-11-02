-- 0004 · Autorización para conservar la HV para futuras vacantes (feedback del patrocinador, 2026-10-27)
-- Crear con: npx supabase migration new autorizacion_futuras

alter table candidatos
  add column acepta_futuras       boolean not null default false,
  add column acepta_futuras_fecha timestamptz;

-- Si acepta, debe quedar la fecha de la autorización (Ley 1581: prueba de la autorización).
alter table candidatos
  add constraint futuras_con_fecha check (acepta_futuras = false or acepta_futuras_fecha is not null);

-- La Reserva Estratégica solo considera candidatos que aceptaron (consulta frecuente).
create index candidatos_reserva_idx on candidatos (estado) where acepta_futuras = true and anonimizado_en is null;

-- Al anonimizar, también se retira la autorización.
-- (Si anonimizar_candidato ya existe en 0002, Justin agrega en esa función:
--   acepta_futuras = false, acepta_futuras_fecha = null
--  mediante CREATE OR REPLACE en una migración nueva, nunca editando la 0002.)
