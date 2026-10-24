import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginForm } from "@/components/admin/LoginForm";

export const metadata: Metadata = {
  title: "Ingresar · Centro de mando",
  robots: { index: false, follow: false },
};

export default function LoginPage() {
  return (
    <main id="contenido" className="grid min-h-dvh place-items-center bg-ink px-4 py-10">
      <div className="w-full max-w-sm rounded-2xl bg-surface p-8 shadow-xl">
        <p className="font-display text-3xl font-extrabold tracking-tight text-ink">immpetus</p>
        <h1 className="mt-6 font-display text-xl font-bold text-ink">Centro de mando</h1>
        <p className="mt-1 text-sm text-ink-soft">Ingresa con tu cuenta corporativa de Google.</p>
        <Suspense>
          <LoginForm />
        </Suspense>
        <p className="mt-6 border-t border-line pt-4 text-xs text-ink-soft">
          Solo cuentas <strong>@immpetus.co</strong> registradas por el líder de selección. Si no tienes acceso, pídelo a tu líder.
        </p>
      </div>
    </main>
  );
}
