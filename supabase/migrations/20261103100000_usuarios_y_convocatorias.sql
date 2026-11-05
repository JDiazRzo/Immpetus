-- Usuarios y convocatorias · Usuarios (último líder protegido) y cierre de convocatorias
-- Crear con: npx supabase migration new usuarios_y_convocatorias

-- ---------- Usuarios: nunca se borran y nunca se queda el sistema sin líder ----------
create or replace function proteger_ultimo_lider() returns trigger language plpgsql as $$
begin
  if old.rol = 'lider' and old.activo
     and (new.rol <> 'lider' or not new.activo)
     and (select count(*) from usuarios where rol = 'lider' and activo and id <> old.id) = 0 then
    raise exception 'Debe quedar al menos un líder activo.';
  end if;
  return new;
end $$;

create trigger usuarios_ultimo_lider
  before update on usuarios
  for each row execute function proteger_ultimo_lider();

create or replace function bloquear_borrado_usuario() returns trigger language plpgsql as $$
begin
  raise exception 'Los usuarios no se borran: se desactivan (activo = false).';
end $$;

create trigger usuarios_sin_borrado
  before delete on usuarios
  for each row execute function bloquear_borrado_usuario();

-- Trazabilidad de cambios de usuarios (quién y cuándo)
alter table usuarios
  add column actualizado_en  timestamptz,
  add column actualizado_por uuid references usuarios(id);

-- ---------- Convocatorias: se cierran, no se eliminan ----------
create type estado_vacante as enum ('abierta', 'cerrada');

alter table vacantes
  add column estado     estado_vacante not null default 'abierta',
  add column cerrada_en timestamptz,
  add column cerrada_por uuid references usuarios(id);

-- Una convocatoria cerrada no puede estar publicada.
alter table vacantes
  add constraint cerrada_no_publicada check (estado = 'abierta' or activa = false);

create index vacantes_estado_idx on vacantes (estado);
