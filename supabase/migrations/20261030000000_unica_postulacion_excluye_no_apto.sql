-- Un candidato descartado (no_apto) puede volver a postularse a la misma vacante (contrato v0.5, 5.9).
drop index candidatos_correo_vacante_unico;
create unique index candidatos_correo_vacante_unico
  on candidatos (vacante_id, lower(correo))
  where anonimizado_en is null and estado <> 'no_apto';
