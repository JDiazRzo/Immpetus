import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ApplyForm } from "@/components/ApplyForm";
import { Container } from "@/components/Container";
import { listarVacantes, obtenerVacante } from "@/lib/api";
import { SITE } from "@/lib/site";
import type { VacanteDetalle } from "@/types/api";

export async function generateStaticParams() {
  const vacantes = await listarVacantes();
  return vacantes.map((v) => ({ slug: v.slug }));
}

export async function generateMetadata(props: PageProps<"/vacantes/[slug]">): Promise<Metadata> {
  const { slug } = await props.params;
  const vacante = await obtenerVacante(slug);
  if (!vacante) return { title: "Vacante no disponible" };
  return {
    title: `${vacante.cargo} en ${vacante.ciudad}`,
    description: `Vacante de ${vacante.cargo} en ${vacante.ciudad}. Postúlese en línea con Immpetus Soluciones.`,
    alternates: { canonical: `/vacantes/${vacante.slug}` },
  };
}

const MODALIDAD_SCHEMA: Record<VacanteDetalle["modalidad"], string | undefined> = {
  remoto: "TELECOMMUTE",
  hibrido: undefined,
  presencial: undefined,
};

function jobPosting(v: VacanteDetalle) {
  return {
    "@context": "https://schema.org",
    "@type": "JobPosting",
    title: v.cargo,
    description: [v.descripcion, ...v.responsabilidades].filter(Boolean).join("\n"),
    datePosted: v.publicada_en,
    employmentType: v.jornada === "Tiempo completo" ? "FULL_TIME" : undefined,
    jobLocationType: MODALIDAD_SCHEMA[v.modalidad],
    hiringOrganization: { "@type": "Organization", name: SITE.name, sameAs: SITE.url },
    jobLocation: {
      "@type": "Place",
      address: { "@type": "PostalAddress", addressLocality: v.ciudad, addressCountry: "CO" },
    },
  };
}

const ICONO = {
  ubicacion: "M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11zm0-8.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
  modalidad: "M3 10.5 12 3l9 7.5M5 9v11h14V9",
  jornada: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zm0-13v4.5l3 2",
  salario: "M12 3v18M16.5 7.5c0-1.7-2-3-4.5-3s-4.5 1.3-4.5 3 2 2.6 4.5 3 4.5 1.3 4.5 3-2 3-4.5 3-4.5-1.3-4.5-3",
  fecha: "M4 6h16v14H4zM4 10h16M8 3v4M16 3v4",
} as const;

function Icono({ d }: { d: string }) {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="size-4 shrink-0" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

// Fecha absoluta: la página se genera estática, así que "hace N días" quedaría desactualizado.
function fechaPublicacion(fecha: string): string {
  return new Date(fecha).toLocaleDateString("es-CO", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "America/Bogota",
  });
}

export default async function VacantePage(props: PageProps<"/vacantes/[slug]">) {
  const { slug } = await props.params;
  const vacante = await obtenerVacante(slug);
  if (!vacante) notFound();

  // `urgente` puede no venir en el detalle según la versión del contrato.
  const urgente = "urgente" in vacante && (vacante as { urgente?: boolean }).urgente === true;
  const datos: Array<[keyof typeof ICONO, string, string]> = [
    ["ubicacion", "Ubicación", vacante.ciudad],
    ["modalidad", "Modalidad", vacante.modalidad_detalle ?? ""],
    ["jornada", "Jornada", vacante.jornada ?? ""],
  ].filter((d): d is [keyof typeof ICONO, string, string] => Boolean(d[2]));

  const seccion = "flex flex-col gap-4 rounded-panel border border-line bg-surface p-6 sm:p-8";
  const tituloBloque = "font-display text-2xl font-bold";

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jobPosting(vacante)).replace(/</g, "\\u003c") }}
      />

      {/* Encabezado de la vacante */}
      <section className="relative bg-ink text-white">
        <Container className="flex flex-col gap-6 pb-24 pt-10 lg:pb-28 lg:pr-[440px]">
          <nav aria-label="Ruta" className="text-sm text-on-ink">
            <Link href="/" className="hover:text-white">Inicio</Link>
            <span aria-hidden="true" className="px-2">/</span>
            <Link href="/#vacantes" className="hover:text-white">Vacantes</Link>
          </nav>

          <div className="flex flex-col gap-4">
            {urgente && (
              <span className="w-fit rounded-full bg-brand-gradient px-3 py-1 text-sm font-bold text-white">
                Selección urgente
              </span>
            )}
            <h1 className="font-display text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-[52px]">
              {vacante.cargo}
            </h1>
            <p className="flex items-center gap-2 text-on-ink">
              <Icono d={ICONO.fecha} />
              Publicada el {fechaPublicacion(vacante.publicada_en)}
            </p>
          </div>

          <dl className="flex flex-wrap gap-2.5">
            {datos.map(([icono, k, v]) => (
              <div key={k} className="flex items-center gap-2 rounded-chip bg-white/10 px-3.5 py-2">
                <Icono d={ICONO[icono]} />
                <dt className="sr-only">{k}</dt>
                <dd className="font-semibold">{v}</dd>
              </div>
            ))}
            <div className="flex items-center gap-2 rounded-chip bg-white/10 px-3.5 py-2">
              <Icono d={ICONO.salario} />
              <dt className="sr-only">Salario</dt>
              <dd className="font-bold tabular-nums">
                {vacante.salario_texto ? (
                  <span className="rounded-[3px] bg-marker px-1.5 text-ink">{vacante.salario_texto}</span>
                ) : (
                  "Salario a convenir"
                )}
              </dd>
            </div>
          </dl>
        </Container>
        <div className="absolute inset-x-0 bottom-0 h-1 bg-brand-gradient" aria-hidden="true" />
      </section>

      <Container className="grid gap-8 pb-28 lg:grid-cols-[1fr_400px] lg:gap-10">
        <article className="relative z-10 -mt-14 flex min-w-0 flex-col gap-6 lg:-mt-16">
          {vacante.descripcion && (
            <section className={seccion}>
              <h2 className={tituloBloque}>El cargo</h2>
              <p className="text-lg leading-relaxed text-ink-soft">{vacante.descripcion}</p>
            </section>
          )}

          {vacante.responsabilidades.length > 0 && (
            <section className={seccion}>
              <h2 className={tituloBloque}>Qué hará</h2>
              <ul className="flex flex-col gap-3">
                {vacante.responsabilidades.map((r, i) => (
                  <li key={i} className="flex gap-3 text-lg leading-relaxed text-ink-soft">
                    <span aria-hidden="true" className="mt-2.5 size-2 shrink-0 rounded-full bg-brand-gradient" />
                    {r}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {vacante.criterios.length > 0 && (
            <section className={seccion}>
              <h2 className={tituloBloque}>Qué buscamos en su hoja de vida</h2>
              <p className="leading-relaxed text-ink-soft">
                Estos son los criterios del cargo. Una persona del equipo revisa cada postulación con ellos.
              </p>
              <ul className="flex flex-wrap gap-2">
                {vacante.criterios.map((c) => (
                  <li
                    key={c.habilidad}
                    className={
                      c.obligatoria
                        ? "rounded-chip border border-action bg-brand-tint px-3 py-1.5 text-[15px] font-semibold text-ink"
                        : "rounded-chip border border-line-strong bg-surface px-3 py-1.5 text-[15px]"
                    }
                  >
                    {c.habilidad}
                    {c.obligatoria && <span className="font-normal text-ink-soft"> · requerido</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="flex flex-col gap-3 rounded-panel border border-dashed border-line-strong p-6 sm:p-8">
            <h2 className="font-display text-xl font-bold">Cómo es el proceso</h2>
            <ol className="grid gap-4 sm:grid-cols-3">
              {[
                ["1", "Se postula", "Con su hoja de vida en PDF. Toma menos de 2 minutos."],
                ["2", "Revisamos", "Un consultor evalúa su perfil frente a los criterios del cargo."],
                ["3", "Le contactamos", "Si su perfil avanza, le escribimos al correo que registró."],
              ].map(([n, t, d]) => (
                <li key={n} className="flex flex-col gap-1">
                  <span className="font-display text-sm font-bold text-action tabular-nums">Paso {n}</span>
                  <span className="font-bold">{t}</span>
                  <span className="text-[15px] leading-relaxed text-ink-soft">{d}</span>
                </li>
              ))}
            </ol>
          </section>

          <Link href="/#vacantes" className="w-fit text-[15px] font-bold text-action hover:underline">
            Ver otras vacantes
          </Link>
        </article>

        <aside
          id="postular"
          className="relative z-10 h-fit min-w-0 scroll-mt-24 rounded-panel border border-line bg-surface p-6 sm:p-8 lg:sticky lg:top-24 lg:-mt-[260px]"
        >
          <ApplyForm vacanteId={vacante.id} />
        </aside>
      </Container>

      {/* Móvil: acceso rápido al formulario */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-surface/95 p-3 backdrop-blur lg:hidden">
        <a
          href="#postular"
          className="flex min-h-12 items-center justify-center rounded-chip bg-action font-bold text-white"
        >
          Postularme a esta vacante
        </a>
      </div>
    </>
  );
}
