"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Video de fondo de la portada (decorativo).
 * - Solo se carga en pantallas ≥ 768 px y sin movimiento reducido; si no, queda la imagen fija.
 * - Botón de pausa visible (WCAG 2.2.2: movimiento automático de más de 5 s).
 */
export function HeroVideo({ mp4, webm, poster }: { mp4: string; webm?: string; poster: string }) {
  const video = useRef<HTMLVideoElement>(null);
  const [activo, setActivo] = useState(false);
  const [pausado, setPausado] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px) and (prefers-reduced-motion: no-preference)");
    const conexion = (navigator as Navigator & { connection?: { saveData?: boolean } }).connection;
    const actualizar = () => setActivo(mq.matches && !conexion?.saveData);
    actualizar();
    mq.addEventListener("change", actualizar);
    return () => mq.removeEventListener("change", actualizar);
  }, []);

  function alternar() {
    const v = video.current;
    if (!v) return;
    if (v.paused) {
      void v.play();
      setPausado(false);
    } else {
      v.pause();
      setPausado(true);
    }
  }

  return (
    <>
      {/* Imagen fija: siempre presente (celular, movimiento reducido, mientras carga) */}
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: `url(${poster})` }}
      />
      {activo && (
        <video
          ref={video}
          autoPlay
          muted
          loop
          playsInline
          preload="auto"
          poster={poster}
          aria-hidden="true"
          className="absolute inset-0 size-full object-cover"
        >
          {webm && <source src={webm} type="video/webm" />}
          <source src={mp4} type="video/mp4" />
        </video>
      )}
      {/* Capa para que el texto blanco se lea: más oscura a la izquierda, donde va el título */}
      <div aria-hidden="true" className="absolute inset-0 bg-gradient-to-r from-ink/95 via-ink/80 to-ink/45" />

      {activo && (
        <button
          type="button"
          onClick={alternar}
          aria-pressed={pausado}
          className="absolute bottom-4 right-4 z-10 inline-flex min-h-11 items-center gap-2 rounded-chip bg-ink/60 px-3 text-sm font-semibold text-white backdrop-blur hover:bg-ink/80"
        >
          <svg viewBox="0 0 24 24" aria-hidden="true" className="size-4" fill="currentColor">
            {pausado ? <path d="M8 5v14l11-7z" /> : <path d="M7 5h4v14H7zM13 5h4v14h-4z" />}
          </svg>
          {pausado ? "Reproducir video" : "Pausar video"}
        </button>
      )}
    </>
  );
}
