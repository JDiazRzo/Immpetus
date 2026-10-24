import Link from "next/link";
import type { VacanteResumen } from "@/types/api";

export function VacancyRow({ vacante }: { vacante: VacanteResumen }) {
  const { slug, cargo, ciudad, modalidad_detalle, jornada, salario_texto, urgente } = vacante;
  return (
    <li className="border-b border-line">
      <Link
        href={`/vacantes/${slug}`}
        className="group grid gap-2 py-6 sm:grid-cols-[2.2fr_1.2fr_1fr_auto] sm:items-center sm:gap-6"
      >
        <span className="flex flex-col gap-1">
          <span className="font-display text-[22px] font-bold leading-tight tracking-tight group-hover:text-action">
            {cargo}
          </span>
          {urgente ? (
            <span className="text-sm font-bold text-review">Selección urgente</span>
          ) : (
            <span className="text-sm text-ink-soft">{jornada}</span>
          )}
        </span>
        <span className="text-ink-soft">
          {ciudad}
          {modalidad_detalle ? `, ${modalidad_detalle.toLowerCase()}` : ""}
        </span>
        <span>
          {salario_texto ? (
            <span className="rounded-[3px] bg-marker px-1.5 py-0.5 font-bold tabular-nums">{salario_texto}</span>
          ) : (
            <span className="text-ink-soft">Salario a convenir</span>
          )}
        </span>
        <span className="text-[15px] font-bold text-action">Ver y postularme</span>
      </Link>
    </li>
  );
}
