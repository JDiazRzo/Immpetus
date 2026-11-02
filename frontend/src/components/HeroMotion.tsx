"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { useRef, type ReactNode } from "react";

gsap.registerPlugin(useGSAP);

/**
 * Animación de la portada, una sola vez al cargar (≤ 1.2 s).
 * El contenido ya está visible en el HTML: gsap.from solo lo trae desde un estado inicial,
 * así que sin JavaScript o con movimiento reducido la portada se ve completa.
 */
export function HeroMotion({ children }: { children: ReactNode }) {
  const scope = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const tl = gsap.timeline({ defaults: { ease: "power3.out", duration: 0.6 } });
        tl.from("[data-hero='kicker']", { y: 12, opacity: 0, duration: 0.4 })
          .from("[data-hero='titulo']", { y: 28, opacity: 0, stagger: 0.12 }, "-=0.2")
          .from("[data-hero='texto']", { y: 16, opacity: 0 }, "-=0.55")
          .from("[data-hero='acciones'] > *", { y: 12, opacity: 0, stagger: 0.06, duration: 0.45 }, "-=0.4")
          .from("[data-hero='cifra']", { y: 12, opacity: 0, stagger: 0.06, duration: 0.45 }, "-=0.35");
      });
      return () => mm.revert();
    },
    { scope },
  );

  return <div ref={scope}>{children}</div>;
}
