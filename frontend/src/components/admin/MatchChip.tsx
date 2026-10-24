import { cn } from "@/lib/cn";

/** Habilidad del candidato. Resaltada solo si coincide con los criterios de la vacante. */
export function MatchChip({ nombre, coincide }: { nombre: string; coincide: boolean }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-chip px-2 py-0.5 text-[13px]",
        coincide ? "bg-marker text-ink" : "border border-line text-ink-soft",
      )}
    >
      {coincide && (
        <svg aria-hidden="true" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 6 9 17l-5-5" />
        </svg>
      )}
      {nombre}
      {coincide && <span className="sr-only"> (coincide con el cargo)</span>}
    </span>
  );
}
