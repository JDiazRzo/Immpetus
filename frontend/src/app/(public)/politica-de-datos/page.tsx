import type { Metadata } from "next";
import { Container } from "@/components/Container";

export const metadata: Metadata = { title: "Política de tratamiento de datos" };

export default function PoliticaDatos() {
  return (
    <Container className="max-w-[760px] py-20">
      <h1 className="font-display text-4xl font-extrabold tracking-tight">Política de tratamiento de datos</h1>
      <p className="mt-6 text-lg leading-relaxed text-ink-soft">
        [Texto oficial de la política de tratamiento de datos personales de Immpetus Soluciones, conforme a la Ley
        1581 de 2012: responsable, finalidades (incluido el análisis de hojas de vida con apoyo de inteligencia
        artificial y revisión humana), derechos del titular y canal de consultas y reclamos.]
      </p>
    </Container>
  );
}
