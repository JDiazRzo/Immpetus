"use client";

import { listarCandidatos, listarVacantesAdmin } from "@/lib/admin-api";
import { useAdmin } from "@/lib/use-admin";
import { CandidateTable } from "../CandidateTable";
import { Estado, Panel } from "../Panel";
import { PageTitle } from "../PageTitle";

export function PorValidar() {
  const candidatos = useAdmin(() => listarCandidatos({ estado: "por_validar" }), []);
  const vacantes = useAdmin(listarVacantesAdmin, []);
  const nombres = Object.fromEntries((vacantes.datos ?? []).map((v) => [v.id, v.cargo]));
  return (
    <>
      <PageTitle titulo="Por validar" antetitulo="Hojas de vida con nota sugerida de 1 a 2. Ninguna se descarta sin su revisión." />
      <Panel>
        <Estado cargando={candidatos.estado === "cargando"} error={candidatos.error} />
        {candidatos.datos && <CandidateTable candidatos={candidatos.datos} vacantes={nombres} vacio="No hay hojas de vida pendientes de validar." />}
      </Panel>
    </>
  );
}
