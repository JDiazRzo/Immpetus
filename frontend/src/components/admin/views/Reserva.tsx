"use client";

import { useId, useState } from "react";
import { buscarReserva, listarHabilidades, listarVacantesAdmin } from "@/lib/admin-api";
import { cn } from "@/lib/cn";
import { useAdmin } from "@/lib/use-admin";
import { CandidateTable } from "../CandidateTable";
import { Estado, Panel } from "../Panel";
import { PageTitle } from "../PageTitle";

export function Reserva() {
  const uid = useId();
  const [seleccion, setSeleccion] = useState<string[]>([]);
  const [cargo, setCargo] = useState("");
  const habilidades = useAdmin(listarHabilidades, []);
  const vacantes = useAdmin(listarVacantesAdmin, []);
  const resultados = useAdmin(() => buscarReserva({ habilidades: seleccion, cargo }), [seleccion.join("|"), cargo]);
  const nombres = Object.fromEntries((vacantes.datos ?? []).map((v) => [v.id, v.cargo]));

  const alternar = (h: string) => setSeleccion((s) => (s.includes(h) ? s.filter((x) => x !== h) : [...s, h]));

  return (
    <>
      <PageTitle titulo="Reserva Estratégica" antetitulo="Perfiles con nota 3 que no encajaron en su vacante, pero sirven para futuras." />
      <Panel className="mb-6">
        <div className="flex flex-col gap-4 p-5">
          <label htmlFor={`${uid}-cargo`} className="flex max-w-md flex-col gap-1.5 text-sm font-semibold">
            Cargo al que se postuló
            <input id={`${uid}-cargo`} type="search" value={cargo} onChange={(e) => setCargo(e.target.value)} placeholder="Ej. soporte" className="min-h-11 rounded-chip border border-line-strong px-3 text-base font-normal" />
          </label>
          <fieldset>
            <legend className="mb-2 text-sm font-semibold">Debe tener todas estas habilidades</legend>
            <Estado cargando={habilidades.estado === "cargando"} />
            <div className="flex flex-wrap gap-2">
              {habilidades.datos?.map((h) => (
                <button
                  key={h.id}
                  type="button"
                  aria-pressed={seleccion.includes(h.nombre)}
                  onClick={() => alternar(h.nombre)}
                  className={cn("min-h-9 rounded-chip px-3 text-sm", seleccion.includes(h.nombre) ? "bg-ink font-semibold text-white" : "border border-line-strong")}
                >
                  {h.nombre}
                </button>
              ))}
            </div>
          </fieldset>
        </div>
      </Panel>
      <Panel titulo={resultados.datos ? `${resultados.datos.length} perfiles en reserva` : "Resultados"}>
        <Estado cargando={resultados.estado === "cargando"} error={resultados.error} />
        {resultados.datos && <CandidateTable candidatos={resultados.datos} vacantes={nombres} vacio="Ningún perfil en reserva cumple esos filtros." />}
      </Panel>
    </>
  );
}
