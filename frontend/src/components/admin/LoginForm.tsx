"use client";

import Script from "next/script";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiRequestError } from "@/lib/api";
import { iniciarSesion } from "@/lib/admin-api";

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

type RespuestaGoogle = { credential: string };
type GoogleId = {
  initialize: (opciones: {
    client_id: string;
    callback: (r: RespuestaGoogle) => void;
    ux_mode?: "popup";
  }) => void;
  renderButton: (
    el: HTMLElement,
    opciones: Record<string, string | number>,
  ) => void;
};
declare global {
  interface Window {
    google?: { accounts: { id: GoogleId } };
  }
}

export function LoginForm() {
  const router = useRouter();
  const destino = useSearchParams().get("next");
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [scriptListo, setScriptListo] = useState(false);
  const contenedor = useRef<HTMLDivElement>(null);

  const ingresar = useCallback(
    async (idToken?: string) => {
      setError(null);
      setCargando(true);
      try {
        await iniciarSesion(idToken ?? "");
        router.replace(destino?.startsWith("/admin") ? destino : "/admin");
      } catch (e) {
        setError(
          e instanceof ApiRequestError
            ? e.message
            : "No pudimos iniciar sesión. Intenta de nuevo.",
        );
        setCargando(false);
      }
    },
    [destino, router],
  );

  useEffect(() => {
    const google = window.google;
    if (!scriptListo || !google || !CLIENT_ID || !contenedor.current) return;
    google.accounts.id.initialize({
      client_id: CLIENT_ID,
      callback: (r) => void ingresar(r.credential),
      ux_mode: "popup",
    });
    google.accounts.id.renderButton(contenedor.current, {
      theme: "outline",
      size: "large",
      text: "continue_with",
      shape: "rectangular",
      width: 320,
      locale: "es",
    });
  }, [scriptListo, ingresar]);

  return (
    <div className="mt-6">
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onReady={() => setScriptListo(true)}
      />
      {!CLIENT_ID ? (
        <Error mensaje="Falta NEXT_PUBLIC_GOOGLE_CLIENT_ID en frontend/.env.local." />
      ) : (
        <div
          ref={contenedor}
          className="flex min-h-11 justify-center"
          aria-busy={cargando}
        />
      )}
      {cargando && (
        <p className="mt-3 text-center text-sm text-ink-soft">
          Verificando tu cuenta…
        </p>
      )}
      <Error mensaje={error} />
    </div>
  );
}

function Error({ mensaje }: { mensaje: string | null }) {
  if (!mensaje) return null;
  return (
    <p
      role="alert"
      className="mt-3 rounded-lg bg-[#FCEDE4] px-3 py-2 text-sm text-review"
    >
      {mensaje}
    </p>
  );
}
