import { ButtonLink } from "@/components/ButtonLink";
import { Container } from "@/components/Container";
import { ContactForm } from "@/components/ContactForm";
import { VacancyList } from "@/components/VacancyList";
import { listarVacantes } from "@/lib/api";
import { SITE } from "@/lib/site";

const CIFRAS = [
  ["+15", "años transformando organizaciones"],
  ["5", "líneas de servicio"],
  ["360°", "gestión del talento"],
  ["LATAM", "cobertura regional"],
] as const;

const SERVICIOS = [
  [
    "Adquisición de talento",
    "Executive search y headhunting, Talento Core, Talento Masivo, Talento Pro, Talento Growth & Tech y Talento Edu & Sales 360.",
  ],
  [
    "Talento BPO",
    "Administración de nómina, Employer of Record para LATAM y staffing.",
  ],
  [
    "Gestión estratégica del talento",
    "Onboarding, KPI de desempeño, compensación y beneficios, cultura y bienestar, offboarding.",
  ],
  [
    "Formación, liderazgo y alto desempeño",
    "Formación en liderazgo, coaching ejecutivo, planes de carrera y evaluación de impacto.",
  ],
  [
    "Diseño y mejoramiento de procesos",
    "Six Sigma, PHVA, Kaizen, diseño de procesos en Bizagi o Visio, sistemas de calidad ISO y gestión del cambio.",
  ],
] as const;

const VENTAJAS = [
  [
    "Ternas en menos tiempo",
    "Cada hoja de vida se clasifica el mismo día en que llega.",
  ],
  [
    "Criterio humano en cada decisión",
    "La tecnología ordena; un consultor evalúa y decide.",
  ],
  [
    "Procesos trazables",
    "Usted ve el avance de su vacante sin pedir reportes.",
  ],
  [
    "Evaluación equitativa",
    "Los mismos criterios para todos los candidatos de un cargo.",
  ],
  [
    "Base de talento propia",
    "Perfiles evaluados y listos para nuevas vacantes.",
  ],
  [
    "Datos protegidos",
    "Tratamiento de información conforme a la Ley 1581 de 2012.",
  ],
] as const;

const tituloSeccion =
  "font-display text-4xl font-extrabold tracking-tight sm:text-[44px]";

export default async function Home() {
  const vacantes = await listarVacantes();

  return (
    <>
      {/* Portada */}
      <section>
        <Container className="flex flex-wrap items-end gap-14 pb-20 pt-20 sm:pt-26">
          <div className="flex min-w-0 flex-[1_1_560px] flex-col gap-7">
            <h1 className="font-display text-5xl font-extrabold leading-none tracking-[-0.035em] sm:text-[66px]">
              Su aliado estratégico en talento humano y gestión organizacional
            </h1>
            <p className="max-w-[600px] text-xl leading-relaxed text-ink-soft">
              Reclutamiento especializado, BPO de nómina, formación ejecutiva y
              diseño de procesos. Soluciones integrales para empresas que
              apuestan por las personas.
            </p>
            <div className="flex flex-wrap gap-3">
              <ButtonLink href="#contacto">
                Necesito talento para mi empresa
              </ButtonLink>
              <ButtonLink href="#vacantes" variant="secondary">
                Busco empleo
              </ButtonLink>
            </div>
          </div>
          <dl className="grid flex-[1_1_280px] grid-cols-2 gap-x-8 gap-y-7 border-l-2 border-ink pl-8">
            {CIFRAS.map(([valor, texto]) => (
              <div key={valor}>
                <dt className="sr-only">{texto}</dt>
                <dd className="font-display text-[42px] font-extrabold leading-none tracking-tight">
                  {valor}
                </dd>
                <dd className="mt-1 text-[15px] text-ink-soft">{texto}</dd>
              </div>
            ))}
          </dl>
        </Container>
      </section>

      {/* Vacantes: el tráfico principal son candidatos, por eso va antes de los servicios */}
      <section id="vacantes" className="scroll-mt-20">
        <Container className="pb-24 pt-8">
          <VacancyList vacantes={vacantes} />
          <p className="mt-7 text-ink-soft">
            ¿Ninguna es para usted?{" "}
            <a
              href={`mailto:${SITE.contacto.seleccionCorreo}`}
              className="font-bold text-action"
            >
              Escríbanos a {SITE.contacto.seleccionCorreo}
            </a>{" "}
            para futuras vacantes.
          </p>
        </Container>
      </section>

      {/* Quiénes somos */}
      <section
        id="nosotros"
        className="scroll-mt-20 border-y border-line bg-surface"
      >
        <Container className="flex flex-wrap gap-16 py-24">
          <h2 className={`${tituloSeccion} flex-[1_1_300px]`}>Quiénes somos</h2>
          <div className="flex min-w-0 flex-[2_1_520px] flex-col gap-6">
            <p className="text-xl leading-relaxed">
              [Misión de Immpetus Soluciones, tal como aparece en la web
              actual.]
            </p>
            <p className="text-lg leading-relaxed text-ink-soft">
              Nuestra promesa: ser los mejores aliados de nuestros clientes en
              el ámbito de la gestión organizacional.
            </p>
          </div>
        </Container>
      </section>

      {/* Servicios */}
      <section id="servicios" className="scroll-mt-20">
        <Container className="py-24">
          <div className="flex flex-wrap items-end justify-between gap-4 border-b-2 border-ink pb-4">
            <h2 className={tituloSeccion}>Cinco líneas de servicio integral</h2>
            <a href="#contacto" className="text-[15px] font-bold text-action">
              Cotizar un servicio
            </a>
          </div>
          <ul>
            {SERVICIOS.map(([nombre, detalle]) => (
              <li
                key={nombre}
                className="grid gap-2 border-b border-line py-7 md:grid-cols-[1fr_2fr] md:gap-8"
              >
                <h3 className="font-display text-2xl font-bold">{nombre}</h3>
                <p className="text-[17px] leading-relaxed text-ink-soft">
                  {detalle}
                </p>
              </li>
            ))}
          </ul>
        </Container>
      </section>

      {/* Ventajas */}
      <section id="ventajas" className="scroll-mt-20 bg-ink text-white">
        <Container className="flex flex-col gap-12 py-24">
          <h2 className={tituloSeccion}>Por qué elegir Immpetus Soluciones</h2>
          <ul className="grid gap-x-12 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
            {VENTAJAS.map(([titulo, texto]) => (
              <li key={titulo} className="flex flex-col gap-2">
                <h3 className="text-xl font-bold">{titulo}</h3>
                <p className="leading-relaxed text-on-ink">{texto}</p>
              </li>
            ))}
          </ul>
        </Container>
      </section>

      {/* Contacto de empresas */}
      <section id="contacto" className="scroll-mt-20 bg-surface">
        <Container className="flex flex-wrap gap-16 py-24">
          <div className="flex flex-[1_1_320px] flex-col gap-8">
            <div className="flex flex-col gap-5">
              <h2 className={tituloSeccion}>Hablemos de su equipo</h2>
              <p className="text-lg leading-relaxed text-ink-soft">
                Cuéntenos qué necesita y un consultor le responde.
              </p>
            </div>
            <div className="leading-loose">
              <h3 className="font-bold">Comercial</h3>
              <a
                href={`mailto:${SITE.contacto.comercialCorreo}`}
                className="text-action"
              >
                {SITE.contacto.comercialCorreo}
              </a>
              <p>{SITE.contacto.comercialTelefono}</p>
            </div>
            <div className="leading-loose">
              <h3 className="font-bold">Selección</h3>
              <a
                href={`mailto:${SITE.contacto.seleccionCorreo}`}
                className="text-action"
              >
                {SITE.contacto.seleccionCorreo}
              </a>
              <p>{SITE.contacto.seleccionTelefono}</p>
            </div>
          </div>
          <div className="relative flex-[2_1_480px]">
            <ContactForm />
          </div>
        </Container>
      </section>
    </>
  );
}
