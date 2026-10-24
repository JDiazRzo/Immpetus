import type { ReactNode } from "react";

export function PageTitle({ antetitulo, titulo, acciones }: { antetitulo?: ReactNode; titulo: string; acciones?: ReactNode }) {
  return (
    <div className="mb-7 flex flex-wrap items-end justify-between gap-5">
      <div className="flex flex-col gap-1.5">
        {antetitulo && <span className="text-sm text-ink-soft">{antetitulo}</span>}
        <h1 className="font-display text-3xl font-extrabold tracking-tight sm:text-[34px]">{titulo}</h1>
      </div>
      {acciones && <div className="flex flex-wrap items-center gap-3">{acciones}</div>}
    </div>
  );
}
