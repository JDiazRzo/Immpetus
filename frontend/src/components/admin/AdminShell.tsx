"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Suspense, type ReactNode } from "react";
import {
  cerrarSesion,
  listarCandidatos,
  listarCorreosSinAsignar,
  obtenerSesion,
} from "@/lib/admin-api";
import { cn } from "@/lib/cn";
import { useAdmin } from "@/lib/use-admin";

const ENLACES = [
  { href: "/admin", label: "Convocatorias", exacto: true },
  {
    href: "/admin/por-validar",
    label: "Por validar",
    contador: "validar" as const,
  },
  { href: "/admin/reserva", label: "Reserva Estratégica" },
  { href: "/admin/panel", label: "Panel gerencial" },
  {
    href: "/admin/correos",
    label: "Correos sin asignar",
    contador: "correos" as const,
  },
];

export function AdminShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const sesion = useAdmin(obtenerSesion, []);
  const porValidar = useAdmin(
    () => listarCandidatos({ estado: "por_validar" }),
    [],
  );
  const correos = useAdmin(listarCorreosSinAsignar, []);
  const contadores = {
    validar: porValidar.datos?.length ?? 0,
    correos: correos.datos?.length ?? 0,
  };
  const salir = async () => {
    await cerrarSesion();
    router.replace("/admin/login");
  };

  return (
    <div className="flex min-h-dvh flex-col bg-paper lg:flex-row">
      <nav
        aria-label="Centro de mando"
        className="sticky top-0 z-20 flex w-full shrink-0 flex-col gap-1 bg-ink px-3.5 py-3 text-on-ink lg:h-dvh lg:w-60 lg:py-5"
      >
        <div className="flex items-center justify-between px-2.5 lg:pb-5">
          <Link
            href="/admin"
            className="flex items-center gap-2.5"
            aria-label="Centro de mando, inicio"
          >
            <span className="grid size-9 place-items-center rounded-chip bg-white">
              <Image
                src="/marca/isotipo.png"
                alt=""
                width={263}
                height={310}
                className="h-6 w-auto"
                priority
              />
            </span>
            <span className="flex flex-col leading-none">
              <span className="font-display text-xl font-extrabold tracking-tight text-white">
                immpe
                <span className="text-brand-gradient brightness-125">tus</span>
              </span>
              <span className="mt-1 hidden text-[11px] font-semibold text-on-ink/80 lg:block">
                Centro de mando
              </span>
            </span>
          </Link>
          <button
            type="button"
            onClick={salir}
            className="min-h-10 rounded-chip px-2 text-sm font-semibold text-on-ink hover:text-white lg:hidden"
          >
            Salir
          </button>
        </div>
        <Suspense fallback={<Enlaces ruta="" contadores={contadores} />}>
          <EnlacesConRuta contadores={contadores} />
        </Suspense>
        <div className="mt-auto hidden border-t border-white/10 pt-4 lg:block">
          {sesion.datos ? (
            <div className="flex items-center gap-3 px-2.5">
              <span
                aria-hidden="true"
                className="grid size-9 shrink-0 place-items-center rounded-full bg-brand-gradient text-sm font-bold text-white"
              >
                {iniciales(sesion.datos.nombre)}
              </span>
              <span className="min-w-0 text-sm">
                <span className="block truncate font-semibold text-white">
                  {sesion.datos.nombre}
                </span>
                <span className="block truncate text-xs text-on-ink">
                  {sesion.datos.correo}
                </span>
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-3 px-2.5" aria-hidden="true">
              <span className="size-9 shrink-0 animate-pulse rounded-full bg-white/10" />
              <span className="flex flex-1 flex-col gap-1.5">
                <span className="h-3 w-3/4 animate-pulse rounded-chip bg-white/10" />
                <span className="h-2.5 w-1/2 animate-pulse rounded-chip bg-white/10" />
              </span>
            </div>
          )}
          <button
            type="button"
            onClick={salir}
            className="mt-3 flex min-h-10 w-full items-center gap-2 rounded-chip px-2.5 text-sm font-semibold text-on-ink hover:bg-white/5 hover:text-white"
          >
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
              className="size-4"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.8}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h11" />
            </svg>
            Cerrar sesión
          </button>
        </div>
      </nav>
      <main
        id="contenido"
        className="relative min-w-0 flex-1 px-4 py-6 sm:px-10 sm:py-8"
      >
        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-0 h-1 bg-brand-gradient"
        />
        {children}
      </main>
    </div>
  );
}

type Contadores = { validar: number; correos: number };

function iniciales(nombre?: string) {
  if (!nombre) return "·";
  return nombre
    .split(/\s+/)
    .filter((p) => /^[A-Za-zÁÉÍÓÚÑáéíóúñ]/.test(p))
    .slice(0, 2)
    .map((p) => p[0]!.toUpperCase())
    .join("");
}

function EnlacesConRuta({ contadores }: { contadores: Contadores }) {
  return <Enlaces ruta={usePathname()} contadores={contadores} />;
}

function Enlaces({
  ruta,
  contadores,
}: {
  ruta: string;
  contadores: Contadores;
}) {
  return (
    <div className="-mx-3.5 flex gap-1 overflow-x-auto px-3.5 [scrollbar-width:none] lg:mx-0 lg:flex-col lg:overflow-visible lg:px-0">
      {ENLACES.map((e) => {
        const activo = e.exacto
          ? ruta === e.href ||
            ruta.startsWith("/admin/vacantes") ||
            ruta.startsWith("/admin/candidatos")
          : ruta.startsWith(e.href);
        const n = e.contador ? contadores[e.contador] : 0;
        return (
          <Link
            key={e.href}
            href={e.href}
            aria-current={activo ? "page" : undefined}
            className={cn(
              "relative flex min-h-11 shrink-0 items-center justify-between gap-2 whitespace-nowrap rounded-chip px-3 text-[15px] transition-colors lg:gap-3",
              activo
                ? "bg-white/10 font-semibold text-white"
                : "hover:bg-white/5 hover:text-white",
            )}
          >
            {activo && (
              <span
                aria-hidden="true"
                className="absolute inset-y-2 left-0 hidden w-1 rounded-full bg-brand-gradient lg:block"
              />
            )}
            {e.label}
            {n > 0 && (
              <span className="rounded-full bg-marker px-2 text-[13px] font-bold text-ink">
                {n}
              </span>
            )}
          </Link>
        );
      })}
    </div>
  );
}
