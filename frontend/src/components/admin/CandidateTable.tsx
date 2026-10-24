import Link from "next/link";
import { cn } from "@/lib/cn";
import type { CandidatoLista } from "@/types/api";
import { MatchChip } from "./MatchChip";
import { ScoreMeter } from "./ScoreMeter";
import { StatusPill } from "./StatusPill";

type Props = { candidatos: CandidatoLista[]; vacantes?: Record<string, string>; vacio: string };

export function CandidateTable({ candidatos, vacantes, vacio }: Props) {
  if (candidatos.length === 0) return <p className="p-6 text-ink-soft">{vacio}</p>;
  return (
    <div className="relative overflow-x-auto">
      <table className="w-full min-w-[880px] border-collapse text-[15px]">
        <thead>
          <tr className="text-left text-sm text-ink-soft">
            <th scope="col" className="px-5 py-3 font-semibold">Candidato</th>
            {vacantes && <th scope="col" className="px-3 py-3 font-semibold">Vacante</th>}
            <th scope="col" className="px-3 py-3 font-semibold">Nota</th>
            <th scope="col" className="px-3 py-3 font-semibold">Habilidades</th>
            <th scope="col" className="px-3 py-3 font-semibold">Estado</th>
            <th scope="col" className="px-5 py-3"><span className="sr-only">Acción</span></th>
          </tr>
        </thead>
        <tbody>
          {candidatos.map((c) => (
            <tr key={c.id} className={cn("border-t border-[#ECEEF4]", c.estado === "por_validar" && "bg-[#FFF9EC]")}>
              <td className="px-5 py-4">
                <strong>{c.nombre}</strong>
                <br />
                <span className="text-[13px] text-ink-soft">{c.canal === "correo" ? "Llegó por correo" : "Postulación web"}</span>
              </td>
              {vacantes && <td className="px-3 py-4 text-ink-soft">{vacantes[c.vacante_id]}</td>}
              <td className="px-3 py-4">
                <ScoreMeter nota={c.nota} validada={c.nota_validada} validadaPor={c.validada_por} />
              </td>
              <td className="max-w-[300px] px-3 py-4">
                <span className="flex flex-wrap gap-1.5">
                  {c.habilidades.length ? c.habilidades.map((h) => <MatchChip key={h.nombre} {...h} />) : <span className="text-sm text-ink-soft">Sin habilidades detectadas</span>}
                </span>
              </td>
              <td className="px-3 py-4"><StatusPill estado={c.estado} /></td>
              <td className="px-5 py-4">
                <Link
                  href={`/admin/candidatos/${c.id}`}
                  className={cn(
                    "inline-flex min-h-10 items-center whitespace-nowrap rounded-chip px-3.5 text-sm font-semibold",
                    c.estado === "por_validar" ? "bg-action text-white" : "border border-line-strong",
                  )}
                >
                  {c.estado === "por_validar" ? "Validar" : "Ver detalle"}
                  <span className="sr-only"> de {c.nombre}</span>
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
