"use client";

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
            className="font-display text-xl font-extrabold tracking-tight text-white lg:text-2xl"
          >
            immpetus
          </Link>
          <button
            type="button"
            onClick={salir}
            className="min-h-10 rounded-chip px-2 text-sm font-semibold text-[#A7ABCB] hover:text-white lg:hidden"
          >
            Salir
          </button>
        </div>
        <Suspense fallback={<Enlaces ruta="" contadores={contadores} />}>
          <EnlacesConRuta contadores={contadores} />
        </Suspense>
        <div className="mt-auto hidden border-t border-[#3A3E80] px-2.5 pt-4 text-sm lg:block">
          {sesion.datos ? (
            <>
              {sesion.datos.nombre}
              <br />
              <span className="text-[#A7ABCB]">{sesion.datos.correo}</span>
            </>
          ) : (
            "…"
          )}
          <button
            type="button"
            onClick={salir}
            className="mt-3 text-xs font-semibold text-[#A7ABCB] underline-offset-2 hover:text-white hover:underline"
          >
            Cerrar sesión
          </button>
        </div>
      </nav>
      <main
        id="contenido"
        className="min-w-0 flex-1 px-4 py-6 sm:px-10 sm:py-8"
      >
        {children}
      </main>
    </div>
  );
}

type Contadores = { validar: number; correos: number };

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
              "flex min-h-11 shrink-0 items-center justify-between gap-2 whitespace-nowrap rounded-chip px-2.5 text-[15px] lg:gap-3",
              activo
                ? "bg-[#2F3373] font-semibold text-white"
                : "hover:bg-[#2A2E6A]",
            )}
          >
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
