-- Esquema inicial · Sistema de selección Immpetus
-- Base: PostgreSQL (Supabase). Ver docs/CONTRATO_API.md y CLAUDE.md.

create extension if not exists "pgcrypto";

-- ---------- Tipos ----------
create type estado_candidato as enum ('nuevo','entrevista','reserva','por_validar','no_apto','contratado');
create type rol_usuario      as enum ('analista','lider','gerencia');
create type canal_postulacion as enum ('web','correo');
create type modalidad_trabajo as enum ('presencial','hibrido','remoto');
create type nivel_habilidad  as enum ('basico','intermedio','avanzado');
create type origen_dato      as enum ('ia','analista');
create type categoria_habilidad as enum ('tecnica','blanda','idioma','herramienta','certificacion');

-- ---------- Usuarios del centro de mando ----------
create table usuarios (
  id         uuid primary key default gen_random_uuid(),
  correo     text not null unique,
  nombre     text not null,
  rol        rol_usuario not null,
  activo     boolean not null default true,
  creado_en  timestamptz not null default now()
);

-- ---------- Vacantes ----------
create table vacantes (
  id                uuid primary key default gen_random_uuid(),
  codigo            text not null unique,              -- ej. GSC-0425 (va en el asunto del correo)
  slug              text not null unique,
  cargo             text not null,
  cliente           text,
  ciudad            text not null,
  modalidad         modalidad_trabajo not null,
  modalidad_detalle text,
  jornada           text,
  salario_texto     text,
  descripcion       text,
  responsabilidades text[] not null default '{}',
  urgente           boolean not null default false,
  activa            boolean not null default false,
  drive_folder_id   text,
  creada_por        uuid references usuarios(id),
  creada_en         timestamptz not null default now(),
  publicada_en      timestamptz
);

-- ---------- Candidatos (una fila por postulación) ----------
create table candidatos (
  id                   uuid primary key default gen_random_uuid(),
  vacante_id           uuid not null references vacantes(id) on delete restrict,
  nombre               text not null,
  correo               text not null,
  celular              text,
  canal                canal_postulacion not null,
  drive_file_id        text,
  drive_url            text,
  archivo_nombre       text,
  estado               estado_candidato not null default 'nuevo',
  autorizacion_datos   boolean not null,
  autorizacion_fecha   timestamptz not null,
  autorizacion_version text not null,
  creado_en            timestamptz not null default now(),
  constraint autorizacion_obligatoria check (autorizacion_datos = true)
);
create index candidatos_vacante_estado_idx on candidatos (vacante_id, estado);

-- ---------- Calificaciones (IA o corrección del analista) ----------
create table calificaciones (
  id            uuid primary key default gen_random_uuid(),
  candidato_id  uuid not null references candidatos(id) on delete cascade,
  nota          smallint not null check (nota between 1 and 5),
  resumen       text,
  matriz        jsonb,
  origen        origen_dato not null,
  modelo_ia     text,
  motivo        text,                                   -- obligatorio si origen = analista
  usuario_id    uuid references usuarios(id),
  fecha         timestamptz not null default now(),
  constraint correccion_con_motivo check (origen = 'ia' or (motivo is not null and usuario_id is not null))
);
create index calificaciones_candidato_idx on calificaciones (candidato_id, fecha desc);

-- ---------- Historial de estados (solo inserción) ----------
create table estados (
  id            uuid primary key default gen_random_uuid(),
  candidato_id  uuid not null references candidatos(id) on delete cascade,
  estado        estado_candidato not null,
  validado_por  uuid references usuarios(id),
  observacion   text,
  fecha         timestamptz not null default now(),
  -- Regla de oro: 'no_apto' y 'contratado' siempre requieren una persona.
  constraint decision_humana check (estado not in ('no_apto','contratado') or validado_por is not null)
);
create index estados_candidato_idx on estados (candidato_id, fecha);

-- ---------- Habilidades ----------
create table habilidades (
  id         uuid primary key default gen_random_uuid(),
  nombre     text not null unique,
  categoria  categoria_habilidad not null
);

create table candidato_habilidades (
  candidato_id      uuid not null references candidatos(id) on delete cascade,
  habilidad_id      uuid not null references habilidades(id) on delete restrict,
  nivel             nivel_habilidad,
  anios_experiencia smallint check (anios_experiencia >= 0),
  origen            origen_dato not null default 'ia',
  primary key (candidato_id, habilidad_id)
);
create index candidato_habilidades_hab_idx on candidato_habilidades (habilidad_id);

create table vacante_habilidades (
  vacante_id    uuid not null references vacantes(id) on delete cascade,
  habilidad_id  uuid not null references habilidades(id) on delete restrict,
  obligatoria   boolean not null default false,
  peso          smallint not null default 1 check (peso between 1 and 5),
  primary key (vacante_id, habilidad_id)
);

-- ---------- Correos que no se pudieron asociar a una vacante ----------
create table correos_sin_asignar (
  id             uuid primary key default gen_random_uuid(),
  gmail_id       text not null unique,
  remitente      text not null,
  asunto         text,
  drive_file_id  text,
  recibido_en    timestamptz not null,
  asignado_a     uuid references candidatos(id),
  creado_en      timestamptz not null default now()
);

-- ---------- Historial inmodificable ----------
create or replace function bloquear_modificacion() returns trigger language plpgsql as $$
begin
  raise exception 'El historial es de solo inserción (%).', tg_table_name;
end $$;

create trigger estados_inmutable       before update or delete on estados       for each row execute function bloquear_modificacion();
create trigger calificaciones_inmutable before update or delete on calificaciones for each row execute function bloquear_modificacion();

-- ---------- Row Level Security ----------
-- El backend usa la service role key (omite RLS). Estas políticas protegen el acceso directo con la anon key.
alter table usuarios              enable row level security;
alter table vacantes              enable row level security;
alter table candidatos            enable row level security;
alter table calificaciones        enable row level security;
alter table estados               enable row level security;
alter table habilidades           enable row level security;
alter table candidato_habilidades enable row level security;
alter table vacante_habilidades   enable row level security;
alter table correos_sin_asignar   enable row level security;

-- Público: solo puede leer vacantes activas.
create policy vacantes_publicas on vacantes for select to anon using (activa = true);

-- Todo lo demás: sin acceso para anon (sin políticas = denegado).
