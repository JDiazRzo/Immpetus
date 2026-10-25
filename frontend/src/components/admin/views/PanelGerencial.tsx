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
    candidatos.datos?.filter(
      (c) => c.vacante_id === vid && (!e || c.estado === e),
    ).length ?? 0;

  return (
    <>
      <PageTitle
        titulo="Panel gerencial"
        antetitulo="Avance de todas las convocatorias, sin pedir reportes."
      />
      <Panel>
        <Estado
          cargando={vacantes.estado === "cargando"}
          error={vacantes.error}
        />
        {vacantes.datos && (
          <ul className="divide-y divide-[#ECEEF4] md:hidden">
            {vacantes.datos.map((v) => (
              <li key={v.id} className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <Link
                      href={`/admin/vacantes/${v.id}`}
                      className="font-semibold hover:text-action"
                    >
                      {v.cargo}
                    </Link>
                    <p className="text-[13px] text-ink-soft">
                      {v.codigo} · {v.activa ? "Publicada" : "Oculta"}
                    </p>
                  </div>
                  <p className="text-right">
                    <span className="block font-display text-2xl font-bold tabular-nums">
                      {cuenta(v.id)}
                    </span>
                    <span className="text-xs text-ink-soft">recibidas</span>
                  </p>
                </div>
                <dl className="mt-3 grid grid-cols-5 gap-1 text-center">
                  {COLUMNAS.map(([e, t]) => (
                    <div
                      key={e}
                      className="flex flex-col-reverse rounded-lg bg-paper px-1 py-2"
                    >
                      <dt className="text-[11px] leading-tight text-ink-soft">
                        {t}
                      </dt>
                      <dd className="font-bold tabular-nums">
                        {cuenta(v.id, e)}
                      </dd>
                    </div>
                  ))}
                </dl>
              </li>
            ))}
          </ul>
        )}
        {vacantes.datos && (
          <div className="relative hidden overflow-x-auto md:block">
            <table className="w-full min-w-[760px] border-collapse text-[15px]">
              <thead>
                <tr className="text-left text-sm text-ink-soft">
                  <th scope="col" className="px-5 py-3 font-semibold">
                    Convocatoria
                  </th>
                  <th
                    scope="col"
                    className="px-3 py-3 text-right font-semibold"
                  >
                    Recibidas
                  </th>
                  {COLUMNAS.map(([, t]) => (
                    <th
                      key={t}
                      scope="col"
                      className="px-3 py-3 text-right font-semibold"
                    >
                      {t}
                    </th>
                  ))}
                  <th scope="col" className="px-5 py-3 font-semibold">
                    Web
                  </th>
                </tr>
              </thead>
              <tbody>
                {vacantes.datos.map((v) => (
                  <tr key={v.id} className="border-t border-[#ECEEF4]">
                    <td className="px-5 py-3.5">
                      <Link
                        href={`/admin/vacantes/${v.id}`}
                        className="font-semibold hover:text-action"
                      >
                        {v.cargo}
                      </Link>
                      <br />
                      <span className="text-[13px] text-ink-soft">
                        {v.codigo} · {v.cliente}
                      </span>
                    </td>
                    <td className="px-3 py-3.5 text-right font-bold tabular-nums">
                      {cuenta(v.id)}
                    </td>
                    {COLUMNAS.map(([e]) => (
                      <td
                        key={e}
                        className="px-3 py-3.5 text-right tabular-nums"
                      >
                        {cuenta(v.id, e)}
                      </td>
                    ))}
                    <td className="px-5 py-3.5 text-sm">
                      {v.activa ? "Publicada" : "Oculta"}
                    </td>
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
