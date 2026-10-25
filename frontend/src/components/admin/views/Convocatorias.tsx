"use client";

import Link from "next/link";
import { actualizarVacante, listarCandidatos, listarVacantesAdmin } from "@/lib/admin-api";
import { useAdmin } from "@/lib/use-admin";
import { Estado, Panel } from "../Panel";
import { PageTitle } from "../PageTitle";
import { PublishToggle } from "../PublishToggle";

export function Convocatorias() {
  const vacantes = useAdmin(listarVacantesAdmin, []);
  const candidatos = useAdmin(() => listarCandidatos(), []);

  const conteo = (id: string) => {
    const cs = candidatos.datos?.filter((c) => c.vacante_id === id) ?? [];
    return { total: cs.length, validar: cs.filter((c) => c.estado === "por_validar").length };
  };

  return (
    <>
      <PageTitle
        titulo="Convocatorias"
        acciones={
          <Link href="/admin/vacantes/nueva" className="inline-flex min-h-11 items-center rounded-chip bg-action px-4 font-bold text-white">
            Nueva vacante
          </Link>
        }
      />
      <Panel>
        <Estado cargando={vacantes.estado === "cargando"} error={vacantes.error} />
        {vacantes.datos && (
          <ul>
            {vacantes.datos.map((v) => {
              const n = conteo(v.id);
              return (
                <li key={v.id} className="flex flex-wrap items-center gap-x-6 gap-y-3 border-t border-[#ECEEF4] px-5 py-4 first:border-t-0">
                  <div className="flex min-w-0 flex-[1_1_320px] flex-col gap-0.5">
                    <Link href={`/admin/vacantes/${v.id}`} className="font-display text-lg font-bold hover:text-action">
                      {v.cargo}
                    </Link>
                    <span className="text-sm text-ink-soft">
                      {v.codigo} · {v.cliente ?? "Sin cliente"} · {v.ciudad}
                    </span>
                  </div>
                  <span className="text-sm tabular-nums">
                    <strong>{n.total}</strong> hojas de vida
                  </span>
                  {n.validar > 0 && (
                    <span className="rounded-full bg-[#FBE7D6] px-2.5 py-1 text-[13px] font-bold text-[#7F3409]">
                      {n.validar} por validar
                    </span>
                  )}
                  <PublishToggle activa={v.activa} onCambiar={(activa) => actualizarVacante(v.id, { activa })} />
                </li>
              );
            })}
          </ul>
        )}
      </Panel>
    </>
  );
}
