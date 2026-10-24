"use client";

import { useCallback, useEffect, useState } from "react";
import { suscribir } from "./admin-api";

type Resultado<T> =
  | { estado: "cargando"; datos: undefined; error: undefined }
  | { estado: "listo"; datos: T; error: undefined }
  | { estado: "error"; datos: undefined; error: string };

/** Carga datos del centro de mando y los recarga cuando algo cambia. */
export function useAdmin<T>(cargar: () => Promise<T>, deps: unknown[]): Resultado<T> & { recargar: () => void } {
  const [res, setRes] = useState<Resultado<T>>({ estado: "cargando", datos: undefined, error: undefined });
  const [version, setVersion] = useState(0);
  const recargar = useCallback(() => setVersion((v) => v + 1), []);

  useEffect(() => suscribir(recargar), [recargar]);

  useEffect(() => {
    let vigente = true;
    cargar()
      .then((datos) => vigente && setRes({ estado: "listo", datos, error: undefined }))
      .catch((e: unknown) =>
        vigente && setRes({ estado: "error", datos: undefined, error: e instanceof Error ? e.message : "Error inesperado." }),
      );
    return () => {
      vigente = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version, ...deps]);

  return { ...res, recargar };
}
