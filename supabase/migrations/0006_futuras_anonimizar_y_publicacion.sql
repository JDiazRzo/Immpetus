-- 0006 · Ajustes que dependen de 0004 y de las reglas de negocio (docs/CONTRATO_API.md v0.5)

-- 1) Al anonimizar también se retira la autorización para futuras vacantes (5.9).
--    CREATE OR REPLACE sobre la función de 0002; no se edita esa migración.
create or replace function anonimizar_candidato(p_candidato uuid, p_usuario uuid)
returns void language plpgsql as $$
begin
  if not exists (select 1 from usuarios where id = p_usuario and rol = 'lider' and activo) then
    raise exception 'Solo un usuario con rol lider puede anonimizar candidatos.';
  end if;

  update candidatos set
    nombre               = 'Titular anonimizado',
    correo               = 'anonimizado+' || id || '@invalid.local',
    celular              = null,
    drive_file_id        = null,
    drive_url            = null,
    archivo_nombre       = null,
    acepta_futuras       = false,
    acepta_futuras_fecha = null,
    anonimizado_en       = now()
  where id = p_candidato and anonimizado_en is null;
end $$;

-- 2) publicada_en se llena la primera vez que una vacante queda activa, venga el cambio de donde venga
--    (backend, seed o edición directa). No se borra al desactivar: conserva la fecha original.
create or replace function fijar_publicada_en()
returns trigger language plpgsql as $$
begin
  if new.activa and new.publicada_en is null then
    new.publicada_en := now();
  end if;
  return new;
end $$;

drop trigger if exists vacantes_publicada_en on vacantes;
create trigger vacantes_publicada_en
  before insert or update of activa, publicada_en on vacantes
  for each row execute function fijar_publicada_en();

-- Listado global de candidatos por estado (GET /api/admin/candidatos) y última nota por candidato.
create index if not exists candidatos_estado_creado_idx on candidatos (estado, creado_en desc);
create index if not exists calificaciones_candidato_fecha_idx on calificaciones (candidato_id, fecha desc);
