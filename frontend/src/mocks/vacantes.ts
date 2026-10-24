// Datos de prueba con el formato del contrato. Las vacantes son las publicadas hoy en immpetus.com;
// los textos entre corchetes son marcadores hasta tener la descripción real.
import type { VacanteDetalle } from "@/types/api";

export const VACANTES_MOCK: VacanteDetalle[] = [
  {
    id: "7b1f2c1e-0001-4c1a-9a01-000000000001",
    slug: "content-manager-estratega-de-marca",
    cargo: "Content Manager, Estratega de Marca",
    ciudad: "Bogotá",
    modalidad: "hibrido",
    modalidad_detalle: "Híbrido",
    jornada: "Tiempo completo",
    salario_texto: null,
    publicada_en: "2026-10-20T13:00:00Z",
    descripcion: "[Propósito del cargo, equipo al que pertenece y principales retos.]",
    responsabilidades: ["[Responsabilidad]", "[Responsabilidad]", "[Responsabilidad]"],
    criterios: [
      { habilidad: "Estrategia de contenido", obligatoria: true },
      { habilidad: "Gestión de marca", obligatoria: true },
      { habilidad: "Redes sociales", obligatoria: false },
    ],
  },
  {
    id: "7b1f2c1e-0002-4c1a-9a01-000000000002",
    slug: "asistente-administrativo-y-financiero",
    cargo: "Asistente Administrativo y Financiero",
    ciudad: "Bogotá",
    modalidad: "presencial",
    modalidad_detalle: "Presencial",
    jornada: "Tiempo completo",
    salario_texto: null,
    publicada_en: "2026-10-18T13:00:00Z",
    descripcion: "[Propósito del cargo, equipo al que pertenece y principales retos.]",
    responsabilidades: ["[Responsabilidad]", "[Responsabilidad]", "[Responsabilidad]"],
    criterios: [
      { habilidad: "Contabilidad básica", obligatoria: true },
      { habilidad: "Excel", obligatoria: true },
    ],
  },
  {
    id: "7b1f2c1e-0003-4c1a-9a01-000000000003",
    slug: "gestor-soporte-servicio-cliente",
    cargo: "Gestor de Soporte y Servicio al Cliente",
    ciudad: "Bogotá, Sabana Norte",
    modalidad: "remoto",
    modalidad_detalle: "80 % remoto",
    jornada: "Tiempo completo",
    salario_texto: "$2.700.000",
    publicada_en: "2026-10-15T13:00:00Z",
    descripcion: "[Propósito del cargo, equipo al que pertenece y principales retos.]",
    responsabilidades: ["[Responsabilidad]", "[Responsabilidad]", "[Responsabilidad]"],
    criterios: [
      { habilidad: "Servicio al cliente", obligatoria: true },
      { habilidad: "Herramientas de tickets", obligatoria: true },
      { habilidad: "Comunicación escrita", obligatoria: false },
    ],
  },
  {
    id: "7b1f2c1e-0004-4c1a-9a01-000000000004",
    slug: "head-of-marketplace-ecommerce",
    cargo: "Head of Marketplace & Ecommerce",
    ciudad: "LATAM",
    modalidad: "remoto",
    modalidad_detalle: "Remoto",
    jornada: "Tiempo completo",
    salario_texto: "USD 2.500+",
    publicada_en: "2026-10-12T13:00:00Z",
    descripcion: "[Propósito del cargo, equipo al que pertenece y principales retos.]",
    responsabilidades: ["[Responsabilidad]", "[Responsabilidad]", "[Responsabilidad]"],
    criterios: [
      { habilidad: "Marketplaces", obligatoria: true },
      { habilidad: "Ecommerce", obligatoria: true },
      { habilidad: "Liderazgo de equipos", obligatoria: false },
    ],
  },
];

/** Vacantes marcadas como urgentes en la web actual. */
export const SLUGS_URGENTES = new Set(["content-manager-estratega-de-marca"]);
