import type { ReactNode } from "react";
import { cn } from "@/lib/cn";
import { EsqueletoChips, EsqueletoLista, EsqueletoPagina } from "./Esqueleto";

export function Panel({
  titulo,
  acciones,
  children,
  className,
}: {
  titulo?: string;
  acciones?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn("rounded-panel border border-line bg-surface", className)}
    >
      {(titulo || acciones) && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4">
          {titulo && (
            <h2 className="font-display text-xl font-bold">{titulo}</h2>
          )}
          {acciones}
        </div>
      )}
      {children}
    </section>
  );
}

type Forma = "lista" | "pagina" | "chips";

export function Estado({
  cargando,
  error,
  forma = "lista",
}: {
  cargando?: boolean;
  error?: string;
  forma?: Forma;
}) {
  if (cargando) {
    if (forma === "pagina") return <EsqueletoPagina />;
    if (forma === "chips") return <EsqueletoChips />;
    return <EsqueletoLista />;
  }
  if (error)
    return (
      <p className="p-6 font-semibold text-review" role="alert">
        {error}
      </p>
    );
  return null;
}
