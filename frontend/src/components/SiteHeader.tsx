import Link from "next/link";
import { ButtonLink } from "./ButtonLink";
import { Container } from "./Container";

const ENLACES = [
  { href: "/#nosotros", label: "Nosotros" },
  { href: "/#servicios", label: "Servicios" },
  { href: "/#ventajas", label: "Ventajas" },
  { href: "/#vacantes", label: "Vacantes" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-surface">
      <Container className="flex items-center justify-between gap-4 py-3">
        {/* Logo provisional hasta tener el archivo oficial */}
        <Link href="/" className="font-display text-2xl font-extrabold tracking-tight text-ink">
          immpetus
        </Link>

        <nav aria-label="Principal" className="hidden items-center gap-6 lg:flex">
          {ENLACES.map((e) => (
            <Link key={e.href} href={e.href} className="text-[15px] font-semibold hover:text-action">
              {e.label}
            </Link>
          ))}
          <ButtonLink href="/#vacantes" variant="secondary">
            Ver vacantes
          </ButtonLink>
          <ButtonLink href="/#contacto">Contáctenos</ButtonLink>
        </nav>

        <details className="relative lg:hidden">
          <summary className="flex min-h-11 cursor-pointer list-none items-center rounded-chip border border-line-strong px-4 font-semibold">
            Menú
          </summary>
          <nav
            aria-label="Principal móvil"
            className="absolute right-0 mt-2 flex w-60 flex-col gap-1 rounded-panel border border-line bg-surface p-2"
          >
            {[...ENLACES, { href: "/#contacto", label: "Contáctenos" }].map((e) => (
              <Link key={e.href} href={e.href} className="rounded-chip px-3 py-3 font-semibold hover:bg-paper">
                {e.label}
              </Link>
            ))}
          </nav>
        </details>
      </Container>
    </header>
  );
}
