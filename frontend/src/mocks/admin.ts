// Base de datos simulada del centro de mando. TODOS los candidatos son ficticios.
// Imita las tablas reales (candidatos, calificaciones, estados) para que las reglas
// de la sección 5 del contrato se puedan probar en el frontend antes de tener backend.
import type { Canal, EstadoCandidato, Habilidad, MatrizIA, UsuarioAdmin, VacanteAdmin } from "@/types/api";
import { VACANTES_MOCK } from "./vacantes";

export const USUARIOS_MOCK: UsuarioAdmin[] = [
  { id: "u-analista", correo: "analista@immpetus.co", nombre: "Analista de RR. HH.", rol: "analista" },
  { id: "u-lider", correo: "lider@immpetus.co", nombre: "Líder de RR. HH.", rol: "lider" },
];

export const HABILIDADES_MOCK: Habilidad[] = [
  ["h1", "Servicio al cliente", "blanda"],
  ["h2", "Herramientas de tickets", "herramienta"],
  ["h3", "Comunicación escrita", "blanda"],
  ["h4", "Zendesk", "herramienta"],
  ["h5", "Inglés B2", "idioma"],
  ["h6", "CRM", "herramienta"],
  ["h7", "Ventas", "tecnica"],
  ["h8", "Estrategia de contenido", "tecnica"],
  ["h9", "Gestión de marca", "tecnica"],
  ["h10", "Redes sociales", "tecnica"],
  ["h11", "Contabilidad básica", "tecnica"],
  ["h12", "Excel", "herramienta"],
  ["h13", "Marketplaces", "tecnica"],
  ["h14", "Ecommerce", "tecnica"],
  ["h15", "Liderazgo de equipos", "blanda"],
  ["h16", "Atención presencial", "blanda"],
].map(([id, nombre, categoria]) => ({ id, nombre, categoria }) as Habilidad);

const idHab = (nombre: string) => HABILIDADES_MOCK.find((h) => h.nombre === nombre)?.id ?? nombre;

const CODIGOS = ["CMM-0420", "AAF-0418", "GSC-0425", "HME-0412"];
const CLIENTES = ["[Cliente A]", "[Cliente B]", "[Cliente C]", "[Cliente D]"];

export function vacantesAdminIniciales(): VacanteAdmin[] {
  return VACANTES_MOCK.map((v, i) => ({
    ...v,
    codigo: CODIGOS[i],
    cliente: CLIENTES[i],
    urgente: i === 0,
    activa: true,
    criterios: v.criterios.map((c) => ({
      habilidad_id: idHab(c.habilidad),
      habilidad: c.habilidad,
      obligatoria: c.obligatoria,
      peso: c.obligatoria ? 3 : 1,
    })),
  }));
}

export type CalificacionRaw = {
  nota: number;
  origen: "ia" | "analista";
  usuario_id: string | null;
  motivo: string | null;
  fecha: string;
};

export type EstadoRaw = {
  estado: EstadoCandidato;
  validado_por: string | null;
  observacion: string | null;
  fecha: string;
};

export type CandidatoRaw = {
  id: string;
  vacante_id: string;
  nombre: string;
  correo: string;
  celular: string;
  canal: Canal;
  creado_en: string;
  habilidades: string[];
  resumen_ia: string;
  matriz: MatrizIA;
  calificaciones: CalificacionRaw[];
  estados: EstadoRaw[];
};

const GSC = VACANTES_MOCK[2].id;
const CMM = VACANTES_MOCK[0].id;
const AAF = VACANTES_MOCK[1].id;
const HME = VACANTES_MOCK[3].id;

const t = (dias: number, horas = 9) => {
  const d = new Date("2026-10-23T00:00:00Z");
  d.setUTCDate(d.getUTCDate() - dias);
  d.setUTCHours(horas + 5);
  return d.toISOString();
};

type Semilla = [string, string, Canal, number, string[], number, string, EstadoCandidato?, boolean?];

// [vacante, nombre, canal, nota IA, habilidades, días atrás, resumen, estado posterior (humano), nota corregida?]
const SEMILLAS: Semilla[] = [
  [GSC, "Laura Gómez", "web", 5, ["Servicio al cliente", "Zendesk", "Inglés B2"], 6, "Cinco años en soporte para empresas de software, manejo de SLA y reportes semanales.", "entrevista"],
  [GSC, "Andrés Rojas", "web", 4, ["Servicio al cliente", "Comunicación escrita", "Herramientas de tickets"], 5, "Tres años en centros de contacto con atención por chat y correo."],
  [GSC, "Camila Torres", "correo", 4, ["Servicio al cliente", "Herramientas de tickets"], 4, "Soporte nivel 1 en una fintech, experiencia con Freshdesk."],
  [GSC, "Julián Martínez", "web", 3, ["Servicio al cliente", "CRM", "Ventas"], 4, "Perfil comercial con experiencia en posventa; poca experiencia en soporte técnico."],
  [GSC, "Valentina Ruiz", "web", 3, ["Comunicación escrita", "Redes sociales"], 3, "Community manager con atención de mensajes de clientes en redes."],
  [GSC, "Felipe Castro", "correo", 2, ["Atención presencial"], 3, "Experiencia en atención presencial en retail; sin experiencia en canales digitales."],
  [GSC, "Sara Mejía", "web", 2, ["Excel"], 2, "Asistente administrativa; no registra experiencia en servicio al cliente."],
  [GSC, "Daniel Pérez", "web", 1, [], 1, "La hoja de vida no menciona experiencia laboral relacionada con el cargo."],
  [CMM, "Mariana López", "web", 5, ["Estrategia de contenido", "Gestión de marca", "Redes sociales"], 5, "Seis años liderando contenido de marca en agencias.", "entrevista"],
  [CMM, "Tomás Herrera", "web", 3, ["Redes sociales", "Comunicación escrita"], 2, "Creador de contenido freelance, sin experiencia en estrategia de marca."],
  [AAF, "Paula Navarro", "web", 4, ["Contabilidad básica", "Excel"], 3, "Tecnóloga contable con dos años como auxiliar administrativa."],
  [AAF, "Ricardo Salas", "correo", 2, ["Atención presencial"], 1, "Experiencia en recepción; no registra manejo contable."],
  [HME, "Natalia Ospina", "web", 5, ["Marketplaces", "Ecommerce", "Liderazgo de equipos", "Inglés B2"], 4, "Gerente de ecommerce regional con manejo de Mercado Libre y Amazon."],
];

export function candidatosIniciales(): CandidatoRaw[] {
  return SEMILLAS.map(([vacante_id, nombre, canal, nota, habilidades, dias, resumen, estadoHumano], i) => {
    const creado = t(dias, 8);
    const calificado = t(dias, 9);
    const inicial: EstadoCandidato = nota >= 4 ? "nuevo" : nota === 3 ? "reserva" : "por_validar";
    const estados: EstadoRaw[] = [
      { estado: "nuevo", validado_por: null, observacion: null, fecha: creado },
      ...(inicial !== "nuevo" ? [{ estado: inicial, validado_por: null, observacion: null, fecha: calificado }] : []),
      ...(estadoHumano
        ? [{ estado: estadoHumano, validado_por: "u-analista", observacion: null, fecha: t(dias - 1, 11) }]
        : []),
    ];
    const slugNombre = nombre.toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "").replace(/\s+/g, ".");
    return {
      id: `c-${String(i + 1).padStart(3, "0")}`,
      vacante_id,
      nombre,
      correo: `${slugNombre}@correo-ficticio.co`,
      celular: `300 000 ${String(1000 + i)}`,
      canal,
      creado_en: creado,
      habilidades,
      resumen_ia: resumen,
      matriz: {
        formacion: "[Formación según la hoja de vida]",
        experiencia_anios: Math.max(0, nota + 1 - (i % 2)),
        sectores: ["[Sector]"],
        justificacion: resumen,
      },
      calificaciones: [{ nota, origen: "ia", usuario_id: null, motivo: null, fecha: calificado }],
      estados,
    };
  });
}

export function correosSinAsignarIniciales() {
  return [
    { id: "m-1", remitente: "postulante.ficticio1@correo-ficticio.co", asunto: "Hoja de vida", archivo_nombre: "HV_2026.pdf", recibido_en: t(0, 7) },
    { id: "m-2", remitente: "postulante.ficticio2@correo-ficticio.co", asunto: "Vacante soporte", archivo_nombre: "curriculum.pdf", recibido_en: t(1, 15) },
  ];
}
