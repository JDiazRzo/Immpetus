"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";

type Props = { activa: boolean; onCambiar: (activa: boolean) => Promise<unknown> };

/**
 * Interruptor optimista: cambia al instante y guarda en segundo plano.
 * Si el backend falla, vuelve al estado anterior y muestra el error.
 */
export function PublishToggle({ activa, onCambiar }: Props) {
  // Valor elegido por el usuario mientras llega el dato real del servidor.
  const [deseado, setDeseado] = useState<boolean | null>(null);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cuando el servidor ya refleja el cambio, se suelta el valor optimista.
  if (deseado !== null && !guardando && deseado === activa) setDeseado(null);
  const visible = deseado ?? activa;

  async function alternar() {
    const nuevo = !visible;
    setDeseado(nuevo);
    setError(null);
    setGuardando(true);
    try {
      await onCambiar(nuevo);
    } catch (e) {
      setDeseado(null);
      setError(e instanceof Error ? e.message : "No se pudo guardar.");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <span className="inline-flex flex-col gap-1">
      <button
        type="button"
        role="switch"
        aria-checked={visible}
        aria-busy={guardando}
        onClick={alternar}
        disabled={guardando}
        className="flex min-h-11 items-center gap-2.5 rounded-chip border border-line bg-surface px-3.5 text-[15px] font-semibold"
      >
        <span aria-hidden="true" className={cn("relative h-[22px] w-10 rounded-full transition-colors", visible ? "bg-ok" : "bg-line-strong")}>
          <span className={cn("absolute top-[3px] size-4 rounded-full bg-white transition-[left]", visible ? "left-[21px]" : "left-[3px]")} />
        </span>
        {visible ? "Publicada en la web" : "Oculta"}
      </button>
      {error && (
        <span role="alert" className="text-xs text-review">
          {error}
        </span>
      )}
    </span>
  );
}
