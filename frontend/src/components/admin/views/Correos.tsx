"use client";

import { useState } from "react";
import { asignarCorreo, listarCorreosSinAsignar, listarVacantesAdmin } from "@/lib/admin-api";
import { useAdmin } from "@/lib/use-admin";
import { Estado, Panel } from "../Panel";
import { PageTitle } from "../PageTitle";

const formato = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short", timeZone: "America/Bogota" });

export function Correos() {
  const correos = useAdmin(listarCorreosSinAsignar, []);
  const vacantes = useAdmin(listarVacantesAdmin, []);
  const [eleccion, setEleccion] = useState<Record<string, string>>({});
  const [mensaje, setMensaje] = useState<string | null>(null);

  async function asignar(id: string) {
    const vacante = eleccion[id];
    if (!vacante) return;
    await asignarCorreo(id, vacante);
    setMensaje("Hoja de vida asignada. Ya aparece en la convocatoria con su nota sugerida.");
  }

  return (
    <>
      <PageTitle titulo="Correos sin asignar" antetitulo="Hojas de vida que llegaron a seleccion@ sin el código de la vacante en el asunto." />
      {mensaje && <p role="status" className="mb-4 font-semibold text-ok">{mensaje}</p>}
      <Panel>
        <Estado cargando={correos.estado === "cargando"} error={correos.error} />
        {correos.datos?.length === 0 && <p className="p-6 text-ink-soft">No hay correos pendientes.</p>}
        <ul>
          {correos.datos?.map((m) => (
            <li key={m.id} className="flex flex-wrap items-center gap-4 border-t border-[#ECEEF4] px-5 py-4 first:border-t-0">
              <div className="flex min-w-0 flex-[1_1_300px] flex-col">
                <strong className="break-all">{m.remitente}</strong>
                <span className="text-sm text-ink-soft">“{m.asunto ?? "Sin asunto"}” · {m.archivo_nombre} · {formato.format(new Date(m.recibido_en))}</span>
              </div>
              <label className="flex items-center gap-2 text-sm font-semibold">
                <span className="sr-only">Vacante para {m.remitente}</span>
                <select value={eleccion[m.id] ?? ""} onChange={(e) => setEleccion((x) => ({ ...x, [m.id]: e.target.value }))} className="min-h-11 rounded-chip border border-line-strong px-2 font-normal">
                  <option value="">Elegir vacante…</option>
                  {vacantes.datos?.map((v) => <option key={v.id} value={v.id}>{v.cargo}</option>)}
                </select>
              </label>
              <button type="button" disabled={!eleccion[m.id]} onClick={() => asignar(m.id)} className="min-h-11 rounded-chip bg-action px-4 font-bold text-white disabled:opacity-50">
                Asignar
              </button>
            </li>
          ))}
        </ul>
      </Panel>
    </>
  );
}
