-- Una sola postulación por correo y vacante. No cuenta a los candidatos anonimizados.
create unique index candidatos_correo_vacante_unico on candidatos (vacante_id, lower(correo))
where
    anonimizado_en is null;