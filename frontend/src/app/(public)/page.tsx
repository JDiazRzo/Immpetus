import { ButtonLink } from "@/components/ButtonLink";
import { Container } from "@/components/Container";
import { ContactForm } from "@/components/ContactForm";
import { HeroMotion } from "@/components/HeroMotion";
import { HeroVideo } from "@/components/HeroVideo";
import { Revelar } from "@/components/Revelar";
import { ServiciosTabs } from "@/components/ServiciosTabs";
import { VentajasCarrusel, type Ventaja } from "@/components/VentajasCarrusel";
import { VacancyList } from "@/components/VacancyList";
import { listarVacantes } from "@/lib/api";
import { SITE } from "@/lib/site";

const CIFRAS = [
  ["+15", "años de experiencia"],
  ["5", "líneas de servicio"],
  ["LATAM", "Colombia y la región"],
] as const;

const PILARES = [
  [
    "+15 años de experiencia",
    "Liderando procesos de transformación organizacional en sectores diversos de Colombia y LATAM.",
  ],
  [
    "Integridad y excelencia",
    "Evaluaciones técnicas y culturales bajo metodologías rigurosas que garantizan la idoneidad del talento.",
  ],
  [
    "Acompañamiento real",
    "Consultoría mano a mano desde el diagnóstico inicial hasta la implementación y adherencia de soluciones.",
  ],
  [
    "Garantía de resultados",
    "Respaldo total con políticas de reemplazo y soporte continuo ante cualquier eventualidad operativa.",
  ],
  [
    "Innovación aplicada",
    "Tecnologías digitales y metodologías ágiles que impulsan la competitividad y el éxito empresarial.",
  ],
] as const;

const VENTAJAS: ReadonlyArray<Ventaja> = [
  {
    icono: "agilidad",
    titulo: "Agilidad",
    texto:
      "Optimizamos la capacidad de respuesta y los tiempos operativos para que avance a la velocidad del mercado.",
  },
  {
    icono: "enfoque",
    titulo: "Enfoque",
    texto:
      "Liberamos su gestión para que se concentre exclusivamente en el core business de su empresa.",
  },
  {
    icono: "respaldo",
    titulo: "Respaldo legal",
    texto:
      "Seguridad jurídica, cumplimiento normativo y blindaje operativo en cada proceso que acompañamos.",
  },
  {
    icono: "talento",
    titulo: "Talento idóneo",
    texto:
      "Perfiles integrales y expertos alineados con su cultura organizacional y objetivos estratégicos.",
  },
  {
    icono: "desempeno",
    titulo: "Alto desempeño",
    texto:
      "Maximizamos la productividad a través de formación especializada y liderazgo estratégico.",
  },
  {
    icono: "excelencia",
    titulo: "Excelencia consultiva",
    texto:
      "Acompañamiento basado en integridad y más de 15 años de experiencia comprobada en Colombia.",
  },
];

const tituloSeccion =
  "font-display text-4xl font-extrabold tracking-tight sm:text-[44px]";
const antetitulo = "text-[15px] font-bold text-action";

export default async function Home() {
  const vacantes = await listarVacantes();

  return (
    <>
      {/* Portada con video de fondo */}
      <section className="relative isolate overflow-hidden bg-ink text-white">
        <HeroVideo
          mp4="/video/hero.mp4"
          webm="/video/hero.webm"
          poster="/video/hero-poster.jpg"
        />
        <HeroMotion>
          <Container className="relative flex min-h-[calc(100svh-73px)] max-h-[860px] flex-col justify-center gap-7 py-20">
            <p data-hero="kicker" className="text-[15px] font-bold text-on-ink">
              Consultoría en talento humano y gestión organizacional
            </p>
            <h1 className="max-w-[760px] font-display text-[44px] font-extrabold leading-[1.02] tracking-[-0.035em] sm:text-[68px]">
              <span data-hero="titulo" className="block">
                Equipo que impulsa
              </span>
              <span data-hero="titulo" className="block">
                el{" "}
                <span className="text-brand-gradient brightness-125">
                  éxito empresarial
                </span>
              </span>
            </h1>
            <p
              data-hero="texto"
              className="max-w-[580px] text-xl leading-relaxed text-on-ink"
            >
              Atraemos, seleccionamos y desarrollamos a las personas que hacen
              crecer a las organizaciones en Colombia y Latinoamérica.
            </p>
            <div data-hero="acciones" className="flex flex-wrap gap-3">
              <ButtonLink href="#vacantes">Ver vacantes abiertas</ButtonLink>
              <ButtonLink href="#contacto" variant="inverse">
                Necesito talento para mi empresa
              </ButtonLink>
            </div>
            <dl className="mt-4 flex flex-wrap gap-x-10 gap-y-5 border-t border-white/15 pt-6">
              {CIFRAS.map(([valor, texto]) => (
                <div
                  key={valor}
                  data-hero="cifra"
                  className="flex flex-col-reverse"
                >
                  <dt className="text-[15px] text-on-ink">{texto}</dt>
                  <dd className="font-display text-4xl font-extrabold leading-none tracking-tight">
                    {valor}
                  </dd>
                </div>
              ))}
            </dl>
          </Container>
        </HeroMotion>
        <div className="relative h-1 bg-brand-gradient" aria-hidden="true" />
      </section>

      <Revelar>
        {/* Quiénes somos */}
        <section id="nosotros" className="scroll-mt-20">
          <Container className="grid gap-14 py-24 lg:grid-cols-[1fr_1.1fr]">
            <div className="flex flex-col gap-6">
              <p data-revelar className={antetitulo}>
                Quiénes somos
              </p>
              <h2 data-revelar className={tituloSeccion}>
                Más que un proveedor, su aliado estratégico
              </h2>
              <p data-revelar className="text-lg leading-relaxed text-ink-soft">
                En Immpetus Soluciones contamos con un equipo de profesionales
                altamente cualificados, dinámicos e innovadores, con más de 15
                años de experiencia en procesos de atracción, selección,
                formación, capacitación y desarrollo organizacional.
              </p>
              <p data-revelar className="text-lg leading-relaxed text-ink-soft">
                Nos encantan los desafíos empresariales. Comprendemos que la
                competitividad de una organización depende de la armonía entre
                sus procesos, su tecnología y su capital humano.
              </p>
              <figure
                data-revelar
                className="relative mt-2 overflow-hidden rounded-panel bg-ink p-7 text-white"
              >
                <div
                  className="absolute inset-y-0 left-0 w-1.5 bg-brand-gradient"
                  aria-hidden="true"
                />
                <figcaption className="font-display text-lg font-bold">
                  Nuestra misión
                </figcaption>
                <blockquote className="mt-2 leading-relaxed text-on-ink">
                  Fomentar el éxito empresarial y aumentar la productividad a
                  través de soluciones consultivas especializadas en gestión
                  organizacional, capital humano, gestión del cambio y cultura,
                  desarrollo digital y aseguramiento de la calidad.
                </blockquote>
              </figure>
            </div>
            <ul className="flex flex-col divide-y divide-line self-center rounded-panel border border-line bg-surface">
              {PILARES.map(([titulo, texto]) => (
                <li
                  key={titulo}
                  data-revelar
                  className="flex flex-col gap-1.5 p-6"
                >
                  <h3 className="font-display text-xl font-bold">{titulo}</h3>
                  <p className="leading-relaxed text-ink-soft">{texto}</p>
                </li>
              ))}
            </ul>
          </Container>
        </section>

        {/* Servicios */}
        <section id="servicios" className="scroll-mt-20 bg-surface">
          <Container className="py-24">
            <div className="flex flex-wrap items-end justify-between gap-6">
              <div data-revelar className="flex max-w-[640px] flex-col gap-4">
                <p className={antetitulo}>Servicios</p>
                <h2 className={tituloSeccion}>
                  Cinco líneas de servicio integral
                </h2>
                <p className="text-lg leading-relaxed text-ink-soft">
                  Soluciones diseñadas para identificar el mejor talento,
                  optimizar la eficiencia operativa y fortalecer el liderazgo de
                  su empresa en Colombia y LATAM.
                </p>
              </div>
            </div>
            <div data-revelar>
              <ServiciosTabs />
            </div>
          </Container>
        </section>

        {/* Ventajas (incluye la promesa de valor: eran los mismos seis puntos) */}
        <section id="ventajas" className="scroll-mt-20 bg-ink text-white">
          <Container className="flex flex-col gap-12 py-24">
            <div data-revelar className="flex max-w-[640px] flex-col gap-4">
              <p className="text-[15px] font-bold text-on-ink">
                Ventajas competitivas
              </p>
              <h2 className={tituloSeccion}>
                Por qué elegir Immpetus Soluciones
              </h2>
            </div>
            <div data-revelar>
              <VentajasCarrusel ventajas={VENTAJAS} />
            </div>
          </Container>
        </section>

        {/* Vacantes: el tráfico principal son candidatos */}
        <section id="vacantes" className="scroll-mt-20">
          <Container className="pb-24 pt-20">
            <VacancyList vacantes={vacantes} />
            <p className="mt-7 text-ink-soft">
              ¿Ninguna es para usted? Al postularse puede autorizarnos a guardar
              su hoja de vida para futuras vacantes.
            </p>
          </Container>
        </section>

        {/* Contacto de empresas */}
        <section id="contacto" className="scroll-mt-20 bg-surface">
          <Container className="flex flex-wrap gap-16 py-24">
            <div className="flex flex-[1_1_320px] flex-col gap-8">
              <div data-revelar className="flex flex-col gap-5">
                <p className={antetitulo}>Contacto</p>
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
      </Revelar>
    </>
  );
}
