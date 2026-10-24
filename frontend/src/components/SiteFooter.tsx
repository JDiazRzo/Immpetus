import { SITE } from "@/lib/site";
import { Container } from "./Container";

export function SiteFooter() {
  return (
    <footer className="bg-ink text-on-ink">
      <Container className="flex flex-wrap items-center justify-between gap-6 py-10 text-[15px]">
        <span className="font-display text-2xl font-extrabold tracking-tight text-white">immpetus</span>
        <span>Bogotá, Colombia</span>
        <a href="/politica-de-datos" className="underline-offset-4 hover:underline">
          Política de tratamiento de datos
        </a>
        <a href={`mailto:${SITE.contacto.seleccionCorreo}`} className="underline-offset-4 hover:underline">
          {SITE.contacto.seleccionCorreo}
        </a>
      </Container>
    </footer>
  );
}
