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

export default async function VacantePage(props: PageProps<"/vacantes/[slug]">) {
  const { slug } = await props.params;
  const vacante = await obtenerVacante(slug);
  if (!vacante) notFound();

  const datos = [
    ["Ubicación", vacante.ciudad],
    ["Modalidad", vacante.modalidad_detalle],
    ["Jornada", vacante.jornada],
  ].filter((d): d is [string, string] => Boolean(d[1]));

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jobPosting(vacante)).replace(/</g, "\\u003c") }}
      />
      <Container className="flex flex-wrap items-start gap-14 pb-28 pt-10">
        <article className="flex min-w-0 flex-[999_1_560px] flex-col gap-10">
          <nav aria-label="Ruta" className="text-sm text-ink-soft">
            <Link href="/" className="hover:text-action">Inicio</Link> /{" "}
            <Link href="/#vacantes" className="hover:text-action">Vacantes</Link>
          </nav>

          <div className="flex flex-col gap-5">
            <h1 className="font-display text-4xl font-extrabold leading-[1.05] tracking-tight sm:text-[54px]">
              {vacante.cargo}
            </h1>
            <dl className="flex flex-wrap gap-x-10 gap-y-4 border-y border-line py-5">
              {datos.map(([k, v]) => (
                <div key={k}>
                  <dt className="text-[13px] text-ink-soft">{k}</dt>
                  <dd className="font-semibold">{v}</dd>
                </div>
              ))}
              <div>
                <dt className="text-[13px] text-ink-soft">Salario</dt>
                <dd className="font-bold tabular-nums">
                  {vacante.salario_texto ? (
                    <span className="rounded-[3px] bg-marker px-1.5">{vacante.salario_texto}</span>
                  ) : (
                    "A convenir"
                  )}
                </dd>
              </div>
            </dl>
            <a
              href="#postular"
              className="inline-flex min-h-11 w-fit items-center rounded-chip bg-action px-5 font-bold text-white lg:hidden"
            >
              Postularme
            </a>
          </div>

          {vacante.descripcion && (
            <section className="flex max-w-[680px] flex-col gap-3">
              <h2 className="font-display text-[26px] font-bold">El cargo</h2>
              <p className="text-lg leading-relaxed text-[#343861]">{vacante.descripcion}</p>
            </section>
          )}

          {vacante.responsabilidades.length > 0 && (
            <section className="flex max-w-[680px] flex-col gap-3">
              <h2 className="font-display text-[26px] font-bold">Qué hará</h2>
              <ul className="list-disc pl-5 text-lg leading-loose text-[#343861]">
                {vacante.responsabilidades.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </section>
          )}

          {vacante.criterios.length > 0 && (
            <section className="flex max-w-[680px] flex-col gap-3">
              <h2 className="font-display text-[26px] font-bold">Con qué comparamos su hoja de vida</h2>
              <p className="leading-relaxed text-ink-soft">
                Estos son los criterios del cargo. Lo que coincida quedará resaltado para quien revise su postulación.
              </p>
              <ul className="flex flex-wrap gap-2">
                {vacante.criterios.map((c) => (
                  <li key={c.habilidad} className="rounded-chip border border-line-strong bg-surface px-3 py-1.5 text-[15px]">
                    {c.habilidad}
                    {c.obligatoria && <span className="text-ink-soft"> (requerido)</span>}
                  </li>
                ))}
              </ul>
            </section>
          )}
        </article>

        <aside
          id="postular"
          className="w-full min-w-0 flex-[1_1_380px] scroll-mt-24 rounded-panel border border-line bg-surface p-6 sm:p-8 lg:sticky lg:top-24"
        >
          <ApplyForm vacanteId={vacante.id} />
        </aside>
      </Container>
    </>
  );
}
