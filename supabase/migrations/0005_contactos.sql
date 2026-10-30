-- 0005 · Formulario de contacto de empresas (landing, sección #contacto)
-- Crear con: npx supabase migration new contactos  (y pegar este contenido)

create type servicio_contacto as enum (
  'adquisicion_talento', 'talento_bpo', 'gestion_estrategica',
  'formacion_liderazgo', 'procesos', 'otro'
);

create table contactos (
  id                   uuid primary key default gen_random_uuid(),
  nombre               text not null check (char_length(nombre) between 3 and 120),
  empresa              text check (char_length(empresa) <= 160),
  correo               text not null check (char_length(correo) <= 254),
  telefono             text check (char_length(telefono) <= 30),
  servicio             servicio_contacto,
  mensaje              text not null check (char_length(mensaje) between 10 and 2000),
  autorizacion_datos   boolean not null,
  autorizacion_fecha   timestamptz not null default now(),
  atendido             boolean not null default false,
  creado_en            timestamptz not null default now(),
  constraint contacto_autorizado check (autorizacion_datos = true)
);

create index contactos_pendientes_idx on contactos (creado_en desc) where atendido = false;

alter table contactos enable row level security;
-- Sin políticas: solo el backend (DATABASE_URL) lee y escribe.
