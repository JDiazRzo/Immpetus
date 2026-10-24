"use client";

import { cn } from "@/lib/cn";

type Props = { activa: boolean; ocupado?: boolean; onCambiar: (activa: boolean) => void };

export function PublishToggle({ activa, ocupado, onCambiar }: Props) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={activa}
      disabled={ocupado}
      onClick={() => onCambiar(!activa)}
      className="flex min-h-11 items-center gap-2.5 rounded-chip border border-line bg-surface px-3.5 text-[15px] font-semibold disabled:opacity-60"
    >
      <span aria-hidden="true" className={cn("relative h-[22px] w-10 rounded-full transition-colors", activa ? "bg-ok" : "bg-line-strong")}>
        <span className={cn("absolute top-[3px] size-4 rounded-full bg-white transition-[left]", activa ? "left-[21px]" : "left-[3px]")} />
      </span>
      {activa ? "Publicada en la web" : "Oculta"}
    </button>
  );
}
