-- 0003 · La bandeja "Correos sin asignar" muestra el nombre del PDF recibido (contrato 2, correos sin asignar).
alter table correos_sin_asignar add column if not exists archivo_nombre text;
