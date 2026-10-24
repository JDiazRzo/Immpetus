-- 0002 · Reglas de negocio acordadas en la revisión de backend (ver docs/CONTRATO_API.md, sección 5).

-- 5.2 · nota, nota_validada y validada_por derivados
create or replace view v_candidatos as
with ultima_cal as (
  select distinct on (candidato_id) candidato_id, nota, origen, usuario_id, fecha
  from calificaciones
  order by candidato_id, fecha desc
),
validacion_estado as (
  select distinct on (e.candidato_id) e.candidato_id, e.validado_por, e.fecha
  from estados e
  join ultima_cal u on u.candidato_id = e.candidato_id
  where e.validado_por is not null and e.fecha >= u.fecha
  order by e.candidato_id, e.fecha desc
)
select
  c.*,
  u.nota,
  (u.origen = 'analista' or ve.validado_por is not null) as nota_validada,
  case
    when u.origen = 'analista' then ua.nombre
    when ve.validado_por is not null then ue.nombre
  end as validada_por
from candidatos c
left join ultima_cal u         on u.candidato_id = c.id
left join validacion_estado ve on ve.candidato_id = c.id
left join usuarios ua          on ua.id = u.usuario_id
left join usuarios ue          on ue.id = ve.validado_por;

-- La vista respeta los permisos de quien consulta (no salta RLS).
alter view v_candidatos set (security_invoker = true);

-- 5.5 · Derecho de supresión: anonimizar sin borrar el historial
alter table candidatos add column if not exists anonimizado_en timestamptz;

create or replace function anonimizar_candidato(p_candidato uuid, p_usuario uuid)
returns void language plpgsql as $$
begin
  if not exists (select 1 from usuarios where id = p_usuario and rol = 'lider' and activo) then
    raise exception 'Solo un usuario con rol lider puede anonimizar candidatos.';
  end if;

  update candidatos set
    nombre        = 'Titular anonimizado',
    correo        = 'anonimizado+' || id || '@invalid.local',
    celular       = null,
    drive_file_id = null,
    drive_url     = null,
    archivo_nombre = null,
    anonimizado_en = now()
  where id = p_candidato and anonimizado_en is null;

  -- Las calificaciones conservan nota y fecha; el resumen y la matriz pueden contener datos personales.
  -- Como calificaciones es de solo inserción, el resumen se deja de exponer desde la API cuando anonimizado_en no es null.
end $$;
-- El borrado del PDF en Drive lo hace el backend (drive.borrar_hv) antes de llamar a esta función.
