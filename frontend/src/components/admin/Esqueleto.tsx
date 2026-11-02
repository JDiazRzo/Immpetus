import { cn } from "@/lib/cn";

/** Bloque gris que reserva el espacio del contenido mientras carga. */
export function Bloque({
  className,
  ancho,
}: {
  className?: string;
  ancho?: number;
}) {
  return (
    <div
      aria-hidden="true"
      className={cn("animate-pulse rounded-chip bg-line/70", className)}
      style={ancho ? { width: ancho } : undefined}
    />
  );
}

/** Filas de una tabla o lista (convocatorias, candidatos, correos). */
export function EsqueletoLista({ filas = 5 }: { filas?: number }) {
  return (
    <div role="status" className="divide-y divide-line">
      <span className="sr-only">Cargando…</span>
      {Array.from({ length: filas }, (_, i) => (
        <div key={i} className="flex items-center gap-4 px-5 py-4">
          <div className="flex min-w-0 flex-1 flex-col gap-2">
            <Bloque className="h-4 w-2/5" />
            <Bloque className="h-3 w-1/4" />
          </div>
          <Bloque className="hidden h-4 w-24 sm:block" />
          <Bloque className="hidden h-6 w-20 rounded-full md:block" />
          <Bloque className="h-10 w-28" />
        </div>
      ))}
    </div>
  );
}

/** Chips (habilidades) mientras carga el catálogo. */
export function EsqueletoChips() {
  return (
    <div role="status" className="flex flex-wrap gap-2 p-5">
      <span className="sr-only">Cargando…</span>
      {[24, 32, 20, 28, 24, 36].map((w, i) => (
        <Bloque key={i} className="h-8" ancho={w * 4} />
      ))}
    </div>
  );
}

/** Página completa: título, contadores y dos paneles. */
export function EsqueletoPagina() {
  return (
    <div role="status" className="flex flex-col gap-6">
      <span className="sr-only">Cargando…</span>
      <div className="flex flex-col gap-3">
        <Bloque className="h-3 w-48" />
        <Bloque className="h-9 w-2/3 max-w-[520px]" />
      </div>
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded-panel border border-line bg-line sm:grid-cols-5">
        {Array.from({ length: 5 }, (_, i) => (
          <div key={i} className="flex flex-col gap-3 bg-surface p-5">
            <Bloque className="h-3 w-20" />
            <Bloque className="h-8 w-10" />
          </div>
        ))}
      </div>
      <div className="rounded-panel border border-line bg-surface">
        <div className="border-b border-line px-5 py-4">
          <Bloque className="h-5 w-32" />
        </div>
        <EsqueletoLista filas={4} />
      </div>
    </div>
  );
}
