import type { Metadata } from "next";
import Image from "next/image";
import { Suspense } from "react";
import { LoginForm } from "@/components/admin/LoginForm";

export const metadata: Metadata = {
  title: "Ingresar · Centro de mando",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return (
    <main
      id="contenido"
      className="relative grid min-h-dvh place-items-center overflow-hidden bg-ink px-4 py-10"
    >
      {/* Halo de marca detrás de la tarjeta */}
      <div
        aria-hidden="true"
        className="absolute left-1/2 top-1/2 size-[640px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand-gradient opacity-25 blur-[120px]"
      />
      <div className="relative w-full max-w-sm overflow-hidden rounded-2xl bg-surface p-8 shadow-xl">
        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-0 h-1.5 bg-brand-gradient"
        />
        <div className="flex items-center gap-3">
          <Image
            src="/marca/isotipo.png"
            alt=""
            width={263}
            height={310}
            className="h-11 w-auto"
            priority
          />
          <Image
            src="/marca/logotipo.png"
            alt="Immpetus"
            width={844}
            height={169}
            className="h-7 w-auto"
            priority
          />
        </div>
        <h1 className="mt-6 font-display text-xl font-bold text-ink">
          Centro de mando
        </h1>
        <p className="mt-1 text-sm text-ink-soft">
          Ingresa con tu cuenta corporativa de Google.
        </p>
        <Suspense>
          <LoginForm />
        </Suspense>
        <p className="mt-6 border-t border-line pt-4 text-xs text-ink-soft">
          Solo cuentas <strong>@immpetus.co</strong> registradas por el líder de
          selección. Si no tienes acceso, pídelo a tu líder.
        </p>
      </div>
    </main>
  );
}
