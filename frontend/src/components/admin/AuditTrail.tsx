import type { EventoHistorial } from "@/types/api";

const formato = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short", timeZone: "America/Bogota" });

export function AuditTrail({ eventos }: { eventos: EventoHistorial[] }) {
  return (
    <ol className="flex flex-col">
      {eventos.map((e, i) => (
        <li key={i} className="grid gap-1 border-t border-line py-3 first:border-t-0 sm:grid-cols-[170px_1fr] sm:gap-4">
          <time dateTime={e.fecha} className="text-sm tabular-nums text-ink-soft">
            {formato.format(new Date(e.fecha))}
          </time>
          <p className="text-[15px] leading-normal">
            {e.detalle}
            {e.usuario && <span className="text-ink-soft"> · {e.usuario}</span>}
          </p>
        </li>
      ))}
    </ol>
  );
}
