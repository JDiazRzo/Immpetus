"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useRef, type ReactNode } from "react";

gsap.registerPlugin(useGSAP, ScrollTrigger);

/**
 * Hace aparecer, al bajar, los elementos marcados con data-revelar dentro de él.
 * - Una sola vez por elemento; escalonado entre los que entran juntos.
 * - El contenido ya está en el HTML y visible: sin JavaScript o con movimiento reducido no se anima.
 * - No usar en la lista de vacantes ni en formularios.
 */
export function Revelar({ children }: { children: ReactNode }) {
  const scope = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        // Lo que ya quedó arriba de la pantalla (entrada por un ancla o recarga a mitad de página) no se oculta.
        const elementos = gsap.utils
          .toArray<HTMLElement>("[data-revelar]")
          .filter(
            (el) => el.getBoundingClientRect().top > window.innerHeight * 0.88,
          );
        gsap.set(elementos, { opacity: 0, y: 24 });
        ScrollTrigger.batch(elementos, {
          start: "top 88%",
          once: true,
          onEnter: (lote) =>
            gsap.to(lote, {
              opacity: 1,
              y: 0,
              duration: 0.6,
              ease: "power3.out",
              stagger: 0.08,
              overwrite: true,
            }),
        });
      });
      return () => mm.revert();
    },
    { scope },
  );

  return <div ref={scope}>{children}</div>;
}
