"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useId, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { LINEAS_SERVICIO } from "@/lib/servicios";

gsap.registerPlugin(useGSAP);

export function ServiciosTabs() {
  const id = useId();
  const [activo, setActivo] = useState(0);
  const botones = useRef<Array<HTMLButtonElement | null>>([]);
  const linea = LINEAS_SERVICIO[activo] ?? LINEAS_SERVICIO[0]!;
  const panel = useRef<HTMLDivElement>(null);
  const anterior = useRef(activo);

  // Transición suave al cambiar de línea (no al cargar la página). Solo transform/opacity.
  useGSAP(
    () => {
      if (anterior.current === activo) return; // al cargar (y en el doble render de desarrollo) no anima
      anterior.current = activo;
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
        tl.from("[data-srv='intro'] > *", { y: 14, opacity: 0, duration: 0.45, stagger: 0.05 })
          .from("[data-srv='destacado']", { x: 24, opacity: 0, duration: 0.5 }, "<0.05")
          .from("[data-srv='item']", { y: 16, opacity: 0, duration: 0.4, stagger: 0.05 }, "<0.1");
      });
      return () => mm.revert();
    },
    { scope: panel, dependencies: [activo] },
  );

  // Teclado de pestañas accesibles: flechas, Inicio y Fin.
  function onKeyDown(e: React.KeyboardEvent) {
    const total = LINEAS_SERVICIO.length;
    const destino =
      e.key === "ArrowRight" || e.key === "ArrowDown"
        ? (activo + 1) % total
        : e.key === "ArrowLeft" || e.key === "ArrowUp"
          ? (activo - 1 + total) % total
          : e.key === "Home"
            ? 0
            : e.key === "End"
              ? total - 1
              : null;
    if (destino === null) return;
    e.preventDefault();
    setActivo(destino);
    botones.current[destino]?.focus();
  }

  return (
    <div className="mt-12 grid gap-6 lg:grid-cols-[300px_1fr] lg:gap-10">
      {/* Móvil: fila deslizable de chips. Escritorio: índice vertical numerado. */}
      <div
        role="tablist"
        aria-label="Líneas de servicio"
        aria-orientation="vertical"
        onKeyDown={onKeyDown}
        className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] lg:mx-0 lg:flex-col lg:gap-1 lg:overflow-visible lg:px-0 lg:pb-0"
      >
        {LINEAS_SERVICIO.map((l, i) => {
          const seleccionado = i === activo;
          return (
            <button
              key={l.id}
              ref={(el) => {
                botones.current[i] = el;
              }}
              type="button"
              role="tab"
              id={`${id}-tab-${i}`}
              aria-selected={seleccionado}
              aria-controls={`${id}-panel`}
              tabIndex={seleccionado ? 0 : -1}
              onClick={() => setActivo(i)}
              className={cn(
                "group relative flex min-h-11 shrink-0 items-center gap-3 rounded-chip text-left transition-colors",
                "px-4 py-2.5 lg:py-4 lg:pl-5",
                seleccionado
                  ? "bg-ink text-white lg:bg-brand-tint lg:text-ink"
                  : "bg-surface text-ink-soft ring-1 ring-line hover:text-ink lg:bg-transparent lg:ring-0 lg:hover:bg-paper",
              )}
            >
              {/* Indicador activo en escritorio */}
              <span
                aria-hidden="true"
                className={cn(
                  "absolute inset-y-2 left-0 hidden w-1 rounded-full lg:block",
                  seleccionado
                    ? "bg-brand-gradient"
                    : "bg-transparent group-hover:bg-line-strong",
                )}
              />
              <span
                className={cn(
                  "font-display text-sm font-bold tabular-nums lg:text-base",
                  seleccionado
                    ? "text-on-ink lg:text-action"
                    : "text-action/70",
                )}
              >
                {l.numero}
              </span>
              <span
                className={cn(
                  "whitespace-nowrap text-[15px] font-semibold lg:whitespace-normal lg:text-base",
                  seleccionado && "lg:font-bold",
                )}
              >
                {l.nombre}
              </span>
            </button>
          );
        })}
      </div>

      <div
        ref={panel}
        role="tabpanel"
        id={`${id}-panel`}
        aria-labelledby={`${id}-tab-${activo}`}
        tabIndex={0}
        className="flex flex-col gap-8 rounded-panel border border-line bg-surface p-6 sm:p-10"
      >
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr] xl:items-start">
          <div data-srv="intro" className="flex flex-col gap-4">
            <h3 className="font-display text-3xl font-extrabold tracking-tight">
              {linea.nombre}
            </h3>
            <p className="text-lg leading-relaxed text-ink-soft">
              {linea.resumen}
            </p>
            <a
              href="#contacto"
              className="inline-flex min-h-11 w-fit items-center rounded-chip bg-action px-5 font-bold text-white"
            >
              Cotizar este servicio
            </a>
          </div>
          <div data-srv="destacado" className="relative overflow-hidden rounded-panel bg-ink p-6 text-white">
            <div
              className="absolute inset-y-0 left-0 w-1.5 bg-brand-gradient"
              aria-hidden="true"
            />
            <p className="font-display text-lg font-bold">
              {linea.destacado.titulo}
            </p>
            <p className="mt-2 leading-relaxed text-on-ink">
              {linea.destacado.texto}
            </p>
          </div>
        </div>

        <ul className="grid content-start gap-x-8 gap-y-6 sm:grid-cols-2 xl:grid-cols-3">
          {linea.items.map((item) => (
            <li
              key={item.titulo}
              data-srv="item"
              className="flex flex-col gap-1.5 border-t-2 border-brand-tint pt-4"
            >
              <h4 className="font-bold">{item.titulo}</h4>
              <p className="text-[15px] leading-relaxed text-ink-soft">
                {item.texto}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
