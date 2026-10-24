"use client";

import Link from "next/link";
import { listarCandidatos, listarVacantesAdmin } from "@/lib/admin-api";
import { useAdmin } from "@/lib/use-admin";
import type { EstadoCandidato } from "@/types/api";
import { Estado, Panel } from "../Panel";
import { PageTitle } from "../PageTitle";

const COLUMNAS: Array<[EstadoCandidato, string]> = [
  ["nuevo", "Nuevos"],
  ["por_validar", "Por validar"],
  ["entrevista", "Entrevista"],
  ["reserva", "Reserva"],
  ["contratado", "Contratados"],
];

export function PanelGerencial() {
  const vacantes = useAdmin(listarVacantesAdmin, []);
  const candidatos = useAdmin(() => listarCandidatos(), []);
  const cuenta = (vid: string, e?: EstadoCandidato) =>
    candidatos.datos?.filter((c) => c.vacante_id === vid && (!e || c.estado === e)).length ?? 0;

  return (
    <>
      <PageTitle titulo="Panel gerencial" antetitulo="Avance de todas las convocatorias, sin pedir reportes." />
      <Panel>
        <Estado cargando={vacantes.estado === "cargando"} error={vacantes.error} />
        {vacantes.datos && (
          <div className="relative overflow-x-auto">
            <table className="w-full min-w-[760px] border-collapse text-[15px]">
              <thead>
                <tr className="text-left text-sm text-ink-soft">
                  <th scope="col" className="px-5 py-3 font-semibold">Convocatoria</th>
                  <th scope="col" className="px-3 py-3 text-right font-semibold">Recibidas</th>
                  {COLUMNAS.map(([, t]) => <th key={t} scope="col" className="px-3 py-3 text-right font-semibold">{t}</th>)}
                  <th scope="col" className="px-5 py-3 font-semibold">Web</th>
                </tr>
              </thead>
              <tbody>
                {vacantes.datos.map((v) => (
                  <tr key={v.id} className="border-t border-[#ECEEF4]">
                    <td className="px-5 py-3.5"><Link href={`/admin/vacantes/${v.id}`} className="font-semibold hover:text-action">{v.cargo}</Link><br /><span className="text-[13px] text-ink-soft">{v.codigo} · {v.cliente}</span></td>
                    <td className="px-3 py-3.5 text-right font-bold tabular-nums">{cuenta(v.id)}</td>
                    {COLUMNAS.map(([e]) => <td key={e} className="px-3 py-3.5 text-right tabular-nums">{cuenta(v.id, e)}</td>)}
                    <td className="px-5 py-3.5 text-sm">{v.activa ? "Publicada" : "Oculta"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </>
  );
}
