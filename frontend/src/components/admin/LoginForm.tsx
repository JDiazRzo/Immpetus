"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { ApiRequestError } from "@/lib/api";
import { iniciarSesion } from "@/lib/admin-api";

export function LoginForm() {
  const router = useRouter();
  const destino = useSearchParams().get("next");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function ingresar() {
    setError(null);
    setCargando(true);
    try {
      // Simulado: aquí irá el botón de Google Identity Services, que entrega el correo verificado.
      await iniciarSesion();
      router.replace(destino?.startsWith("/admin") ? destino : "/admin");
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : "No pudimos iniciar sesión. Intenta de nuevo.");
      setCargando(false);
    }
  }

  return (
    <div className="mt-6">
      <button
        type="button"
        onClick={ingresar}
        disabled={cargando}
        className="flex w-full items-center justify-center gap-3 rounded-lg border border-line-strong bg-surface px-4 py-3 font-semibold text-ink transition-colors hover:bg-paper disabled:opacity-60"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24" className="size-5">
          <path fill="#4285F4" d="M22.5 12.3c0-.8-.1-1.5-.2-2.3H12v4.3h5.9a5 5 0 0 1-2.2 3.3v2.7h3.6c2-1.9 3.2-4.7 3.2-8z" />
          <path fill="#34A853" d="M12 23c3 0 5.5-1 7.3-2.7l-3.6-2.7c-1 .7-2.2 1-3.7 1-2.9 0-5.3-1.9-6.2-4.5H2.1v2.8A11 11 0 0 0 12 23z" />
          <path fill="#FBBC05" d="M5.8 14.1a6.6 6.6 0 0 1 0-4.2V7.1H2.1a11 11 0 0 0 0 9.8z" />
          <path fill="#EA4335" d="M12 5.4c1.6 0 3.1.6 4.2 1.7l3.2-3.2A11 11 0 0 0 2.1 7.1l3.7 2.8C6.7 7.3 9.1 5.4 12 5.4z" />
        </svg>
        {cargando ? "Ingresando…" : "Continuar con Google"}
      </button>
      {error && (
        <p role="alert" className="mt-3 rounded-lg bg-[#FCEDE4] px-3 py-2 text-sm text-review">
          {error}
        </p>
      )}
    </div>
  );
}
