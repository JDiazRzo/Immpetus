"use client";

import Link from "next/link";
import { useId, useState } from "react";
import { actualizarVacante, enviarReporte, listarCandidatos, obtenerVacanteAdmin, resumenVacante } from "@/lib/admin-api";
import { ETIQUETA_ESTADO } from "@/lib/estados";
import { cn } from "@/lib/cn";
import { useAdmin } from "@/lib/use-admin";
import type { EstadoCandidato } from "@/types/api";
import { CandidateTable } from "../CandidateTable";
import { Estado, Panel } from "../Panel";
import { PageTitle } from "../PageTitle";
import { PublishToggle } from "../PublishToggle";

const FILTROS: Array<EstadoCandidato | "todos"> = ["todos", "por_validar", "nuevo", "entrevista", "reserva", "no_apto", "contratado"];

export function Convocatoria({ id }: { id: string }) {
  const vacante = useAdmin(() => obtenerVacanteAdmin(id), [id]);
  const resumen = useAdmin(() => resumenVacante(id), [id]);
  const [filtro, setFiltro] = useState<EstadoCandidato | "todos">("todos");
  const candidatos = useAdmin(() => listarCandidatos({ vacante_id: id, estado: filtro === "todos" ? undefined : filtro }), [id, filtro]);
  const [reporteAbierto, setReporteAbierto] = useState(false);

  if (vacante.estado !== "listo") return <Estado cargando={vacante.estado === "cargando"} error={vacante.error} />;
  const v = vacante.datos;
  const r = resumen.datos;

  const tarjetas = [
    ["Recibidas", r?.recibidas, "text-ink"],
    ["Nota 4 a 5", r?.nota_4_5, "text-ok"],
    ["Reserva (nota 3)", r?.reserva, "text-reserve"],
    ["Por validar (1 a 2)", r?.por_validar, "text-review"],
    ["En entrevista", r?.entrevista, "text-ink"],
  ] as const;

  return (
    <>
      <PageTitle
        antetitulo={<>Convocatoria {v.codigo} · {v.cliente ?? "Sin cliente"} · <Link href={`/admin/vacantes/${v.id}/editar`} className="font-semibold text-action">Editar vacante</Link></>}
        titulo={v.cargo}
        acciones={
          <>
            <PublishToggle activa={v.activa} onCambiar={(activa) => actualizarVacante(v.id, { activa })} />
            <button type="button" onClick={() => setReporteAbierto((x) => !x)} aria-expanded={reporteAbierto} className="min-h-11 rounded-chip bg-action px-4 font-bold text-white">
              Enviar reporte a gerencia
            </button>
          </>
        }
      />

      {reporteAbierto && <FormReporte vacanteId={v.id} onCerrar={() => setReporteAbierto(false)} />}

      <dl className="mb-7 grid grid-cols-2 overflow-hidden rounded-panel border border-line bg-surface sm:grid-cols-5">
        {tarjetas.map(([etiqueta, valor, color]) => (
          <div key={etiqueta} className="border-b border-r border-line px-5 py-4 sm:border-b-0 sm:last:border-r-0">
            <dt className="text-sm text-ink-soft">{etiqueta}</dt>
            <dd className={cn("font-display text-[34px] font-extrabold tabular-nums", color)}>{valor ?? "–"}</dd>
          </div>
        ))}
      </dl>

      <Panel
        titulo="Candidatos"
        acciones={<span className="text-sm text-ink-soft">Ordenados por nota. Resaltado: coincide con el cargo.</span>}
      >
        <div role="group" aria-label="Filtrar por estado" className="flex flex-wrap gap-2 border-b border-line px-5 py-3">
          {FILTROS.map((f) => (
            <button
              key={f}
              type="button"
              aria-pressed={filtro === f}
              onClick={() => setFiltro(f)}
              className={cn("min-h-9 rounded-full px-3 text-sm font-semibold", filtro === f ? "bg-ink text-white" : "border border-line-strong")}
            >
              {f === "todos" ? "Todos" : ETIQUETA_ESTADO[f]}
            </button>
          ))}
        </div>
        <Estado cargando={candidatos.estado === "cargando"} error={candidatos.error} />
        {candidatos.datos && <CandidateTable candidatos={candidatos.datos} vacio="No hay candidatos en este estado." />}
      </Panel>
    </>
  );
}

function FormReporte({ vacanteId, onCerrar }: { vacanteId: string; onCerrar: () => void }) {
  const id = useId();
  const [correos, setCorreos] = useState("gerencia@immpetus.co");
  const [estado, setEstado] = useState<"inicial" | "enviando" | "enviado" | string>("inicial");

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setEstado("enviando");
    try {
      const lista = correos.split(",").map((c) => c.trim()).filter(Boolean);
      await enviarReporte(vacanteId, lista);
      setEstado("enviado");
    } catch (err) {
      setEstado(err instanceof Error ? err.message : "No se pudo enviar el reporte.");
    }
  }

  return (
    <Panel className="mb-7">
      <form onSubmit={enviar} className="flex flex-wrap items-end gap-4 p-5">
        <label htmlFor={id} className="flex flex-[1_1_320px] flex-col gap-1.5 text-sm font-semibold">
          Destinatarios (separados por coma)
          <input id={id} value={correos} onChange={(e) => setCorreos(e.target.value)} className="min-h-11 rounded-chip border border-line-strong px-3 text-base font-normal" />
        </label>
        <button type="submit" disabled={estado === "enviando"} className="min-h-11 rounded-chip bg-action px-4 font-bold text-white disabled:opacity-60">
          {estado === "enviando" ? "Enviando reporte…" : "Enviar reporte"}
        </button>
        <button type="button" onClick={onCerrar} className="min-h-11 rounded-chip border border-line-strong px-4 font-semibold">
          Cancelar
        </button>
        <p role="status" className="w-full text-sm">
          {estado === "enviado" && <span className="font-semibold text-ok">Reporte enviado con el ranking actual.</span>}
          {!["inicial", "enviando", "enviado"].includes(estado) && <span className="font-semibold text-review">{estado}</span>}
          {estado === "inicial" && <span className="text-ink-soft">Incluye ranking, datos de contacto, resumen del perfil y enlace a Drive.</span>}
        </p>
      </form>
    </Panel>
  );
}
