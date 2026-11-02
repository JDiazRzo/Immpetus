"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { cn } from "@/lib/cn";

gsap.registerPlugin(useGSAP);

export type Icono =
  | "agilidad"
  | "enfoque"
  | "respaldo"
  | "talento"
  | "desempeno"
  | "excelencia";
export type Ventaja = { icono: Icono; titulo: string; texto: string };

const TRAZOS: Record<Icono, string> = {
  agilidad: "M13 2 4 14h7l-1 8 9-12h-7l1-8z",
  enfoque:
    "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zm0-4a5 5 0 1 0 0-10 5 5 0 0 0 0 10zm0-4a1 1 0 1 0 0-2 1 1 0 0 0 0 2z",
  respaldo:
    "M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3zm-3 10 2 2 4-4",
  talento:
    "M16 20v-1a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v1M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zm13 9v-1a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8",
  desempeno: "M3 17l6-6 4 4 8-8M15 7h6v6",
  excelencia:
    "M8 21h8M12 17v4M7 4h10v4a5 5 0 0 1-10 0V4zM17 6h3v1a3 3 0 0 1-3 3M7 6H4v1a3 3 0 0 0 3 3",
};

const INTERVALO_MS = 6000;

/**
 * Carrusel de ventajas: una a la vez, pasa sola cada 6 s y se puede mover con flechas,
 * puntos, teclado o deslizando. Se detiene al pasar el mouse, al enfocar o con el botón de pausa
 * (WCAG 2.2.2), y no avanza solo si el usuario pidió movimiento reducido.
 */
export function VentajasCarrusel({
  ventajas,
}: {
  ventajas: ReadonlyArray<Ventaja>;
}) {
  const id = useId();
  const scope = useRef<HTMLDivElement>(null);
  const [actual, setActual] = useState(0);
  const [direccion, setDireccion] = useState<1 | -1>(1);
  const [pausado, setPausado] = useState(false);
  const [enfocado, setEnfocado] = useState(false);
  const [reducido, setReducido] = useState(false);
  const toque = useRef<number | null>(null);
  const total = ventajas.length;
  const ventaja = ventajas[actual] ?? ventajas[0]!;

  const ir = useCallback(
    (destino: number, dir: 1 | -1) => {
      setDireccion(dir);
      setActual(((destino % total) + total) % total);
    },
    [total],
  );
  const siguiente = useCallback(() => ir(actual + 1, 1), [actual, ir]);
  const anterior = useCallback(() => ir(actual - 1, -1), [actual, ir]);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const actualizar = () => setReducido(mq.matches);
    actualizar();
    mq.addEventListener("change", actualizar);
    return () => mq.removeEventListener("change", actualizar);
  }, []);

  const corriendo = !pausado && !enfocado && !reducido;
  useEffect(() => {
    if (!corriendo) return;
    const t = window.setTimeout(siguiente, INTERVALO_MS);
    return () => window.clearTimeout(t);
  }, [corriendo, siguiente]);

  // Desliza la diapositiva nueva desde el lado hacia donde se avanza.
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from("[data-slide]", {
          xPercent: 12 * direccion,
          opacity: 0,
          duration: 0.55,
          ease: "power3.out",
        });
        gsap.from("[data-slide] > *", {
          x: 24 * direccion,
          opacity: 0,
          stagger: 0.06,
          duration: 0.5,
          ease: "power3.out",
          delay: 0.05,
        });
      });
      return () => mm.revert();
    },
    { scope, dependencies: [actual] },
  );

  const anteriorIdx = (actual - 1 + total) % total;
  const siguienteIdx = (actual + 1) % total;

  return (
    <div
      ref={scope}
      role="region"
      aria-roledescription="carrusel"
      aria-label="Ventajas competitivas"
      className="flex flex-col gap-8"
      onMouseEnter={() => setPausado(true)}
      onMouseLeave={() => setPausado(false)}
      onFocusCapture={() => setEnfocado(true)}
      onBlurCapture={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null))
          setEnfocado(false);
      }}
      onKeyDown={(e) => {
        if (e.key === "ArrowRight") siguiente();
        if (e.key === "ArrowLeft") anterior();
      }}
    >
      <div className="grid items-stretch gap-4 lg:grid-cols-[0.6fr_2fr_0.6fr]">
        {/* Vecinos a los lados: anticipan que hay más y se pueden tocar */}
        <button
          type="button"
          onClick={anterior}
          aria-label={`Anterior: ${ventajas[anteriorIdx]?.titulo}`}
          className="hidden flex-col justify-center gap-3 overflow-hidden rounded-panel border border-white/10 p-6 text-left opacity-50 transition-opacity hover:opacity-80 lg:flex"
        >
          <IconoCaja icono={ventajas[anteriorIdx]!.icono} />
          <span className="text-lg font-bold">
            {ventajas[anteriorIdx]?.titulo}
          </span>
        </button>

        <div
          className="relative min-h-[300px] overflow-hidden rounded-panel bg-white/[0.06] p-8 sm:p-12"
          onTouchStart={(e) => {
            toque.current = e.touches[0]?.clientX ?? null;
          }}
          onTouchEnd={(e) => {
            const inicio = toque.current;
            const fin = e.changedTouches[0]?.clientX;
            toque.current = null;
            if (inicio == null || fin == null || Math.abs(fin - inicio) < 40)
              return;
            if (fin < inicio) siguiente();
            else anterior();
          }}
        >
          <div
            className="absolute inset-x-0 top-0 h-1 bg-brand-gradient"
            aria-hidden="true"
          />
          <div
            key={actual}
            data-slide
            id={`${id}-slide`}
            role="group"
            aria-roledescription="diapositiva"
            aria-label={`${actual + 1} de ${total}: ${ventaja.titulo}`}
            className="flex flex-col gap-5"
          >
            <IconoCaja icono={ventaja.icono} grande />
            <p className="font-display text-sm font-bold tabular-nums text-on-ink">
              {String(actual + 1).padStart(2, "0")} /{" "}
              {String(total).padStart(2, "0")}
            </p>
            <h3 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">
              {ventaja.titulo}
            </h3>
            <p className="max-w-[560px] text-lg leading-relaxed text-on-ink">
              {ventaja.texto}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={siguiente}
          aria-label={`Siguiente: ${ventajas[siguienteIdx]?.titulo}`}
          className="hidden flex-col justify-center gap-3 overflow-hidden rounded-panel border border-white/10 p-6 text-left opacity-50 transition-opacity hover:opacity-80 lg:flex"
        >
          <IconoCaja icono={ventajas[siguienteIdx]!.icono} />
          <span className="text-lg font-bold">
            {ventajas[siguienteIdx]?.titulo}
          </span>
        </button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <div
          className="flex items-center gap-1"
          role="group"
          aria-label="Elegir ventaja"
        >
          {ventajas.map((v, i) => (
            <button
              key={v.titulo}
              type="button"
              onClick={() => ir(i, i >= actual ? 1 : -1)}
              aria-label={`Ver ${v.titulo}`}
              aria-current={i === actual ? "true" : undefined}
              className="grid size-11 place-items-center"
            >
              <span
                className={cn(
                  "block h-1.5 rounded-full transition-all",
                  i === actual ? "w-8 bg-brand-gradient" : "w-3 bg-white/30",
                )}
              />
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <Flecha
            onClick={anterior}
            etiqueta="Ventaja anterior"
            d="M15 18l-6-6 6-6"
          />
          <Flecha
            onClick={siguiente}
            etiqueta="Ventaja siguiente"
            d="M9 18l6-6-6-6"
          />
        </div>
      </div>
      <p className="sr-only" aria-live={corriendo ? "off" : "polite"}>
        {ventaja.titulo}
      </p>
    </div>
  );
}

function IconoCaja({ icono, grande }: { icono: Icono; grande?: boolean }) {
  return (
    <span
      className={cn(
        "grid place-items-center rounded-chip bg-white/10 text-white",
        grande ? "size-14" : "size-11",
      )}
    >
      <svg
        viewBox="0 0 24 24"
        aria-hidden="true"
        className={grande ? "size-7" : "size-6"}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.8}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d={TRAZOS[icono]} />
      </svg>
    </span>
  );
}

function Flecha({
  onClick,
  etiqueta,
  d,
}: {
  onClick: () => void;
  etiqueta: string;
  d: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={etiqueta}
      className="grid size-11 place-items-center rounded-chip border border-white/20 text-white hover:border-white/50"
    >
      <svg
        viewBox="0 0 24 24"
        aria-hidden="true"
        className="size-5"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d={d} />
      </svg>
    </button>
  );
}
