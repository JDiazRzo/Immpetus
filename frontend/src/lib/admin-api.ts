// Cliente del centro de mando (/api/admin). Hoy responde desde una base simulada en memoria
// que aplica las mismas reglas del contrato v0.2 (sección 5). Al conectar el backend,
// cada función se reemplaza por su llamada HTTP sin cambiar las páginas.
import {
  type CandidatoRaw,
  candidatosIniciales,
  correosSinAsignarIniciales,
  HABILIDADES_MOCK,
  USUARIOS_MOCK,
  vacantesAdminIniciales,
} from "@/mocks/admin";
import type {
  CandidatoDetalle,
  CandidatoLista,
  CorreoSinAsignar,
  EstadoCandidato,
  EventoHistorial,
  Habilidad,
  ResumenVacante,
  UsuarioAdmin,
  VacanteAdmin,
  VacanteInput,
} from "@/types/api";
import { ApiRequestError } from "./api";
import { ETIQUETA_ESTADO, estadoInicialPorNota, puedeTransitar } from "./estados";

// ---------- Base simulada ----------
const db = {
  vacantes: vacantesAdminIniciales(),
  candidatos: candidatosIniciales(),
  correos: correosSinAsignarIniciales() as CorreoSinAsignar[],
};

const oyentes = new Set<() => void>();
export function suscribir(fn: () => void) {
  oyentes.add(fn);
  return () => {
    oyentes.delete(fn);
  };
}
const notificar = () => oyentes.forEach((fn) => fn());
const espera = () => new Promise((r) => setTimeout(r, 150));

// Sesión simulada. Se reemplaza por el login con Google restringido al dominio.
const USUARIO_ACTUAL = USUARIOS_MOCK[0];
const nombreUsuario = (id: string | null) => USUARIOS_MOCK.find((u) => u.id === id)?.nombre ?? null;

// ---------- Derivaciones (equivalen a la vista v_candidatos) ----------
function ultimaCalificacion(c: CandidatoRaw) {
  return c.calificaciones.at(-1) ?? null;
}

function estadoActual(c: CandidatoRaw): EstadoCandidato {
  return c.estados.at(-1)?.estado ?? "nuevo";
}

function validacion(c: CandidatoRaw): { validada: boolean; por: string | null } {
  const cal = ultimaCalificacion(c);
  if (!cal) return { validada: false, por: null };
  if (cal.origen === "analista") return { validada: true, por: nombreUsuario(cal.usuario_id) };
  const humano = [...c.estados].reverse().find((e) => e.validado_por && e.fecha >= cal.fecha);
  return humano ? { validada: true, por: nombreUsuario(humano.validado_por) } : { validada: false, por: null };
}

function archivoNombre(c: CandidatoRaw, v: VacanteAdmin | undefined) {
  const nota = ultimaCalificacion(c)?.nota ?? 0;
  return `${nota} - ${c.nombre} - ${v?.cargo ?? "Cargo"}.pdf`;
}

function aLista(c: CandidatoRaw): CandidatoLista {
  const vacante = db.vacantes.find((v) => v.id === c.vacante_id);
  const criterios = new Set(vacante?.criterios.map((k) => k.habilidad));
  const { validada, por } = validacion(c);
  return {
    id: c.id,
    vacante_id: c.vacante_id,
    nombre: c.nombre,
    correo: c.correo,
    celular: c.celular,
    canal: c.canal,
    drive_url: "#",
    archivo_nombre: archivoNombre(c, vacante),
    nota: ultimaCalificacion(c)?.nota ?? null,
    nota_validada: validada,
    validada_por: por,
    estado: estadoActual(c),
    habilidades: c.habilidades.map((nombre) => ({ nombre, coincide: criterios.has(nombre) })),
    creado_en: c.creado_en,
  };
}

function historial(c: CandidatoRaw): EventoHistorial[] {
  const eventos: EventoHistorial[] = [
    {
      fecha: c.creado_en,
      evento: "postulacion_recibida",
      detalle: c.canal === "web" ? "Postulación desde la web. Autorización de datos v1.0 aceptada." : "Hoja de vida recibida por correo (autorización correo-1.0).",
      usuario: null,
    },
    { fecha: c.creado_en, evento: "hv_guardada", detalle: "Hoja de vida guardada en Drive con nombre estándar.", usuario: null },
    ...c.calificaciones.map<EventoHistorial>((k) =>
      k.origen === "ia"
        ? { fecha: k.fecha, evento: "calificacion_ia", detalle: `Nota sugerida por IA: ${k.nota}.`, usuario: null }
        : { fecha: k.fecha, evento: "calificacion_analista", detalle: `Nota corregida a ${k.nota}. Motivo: ${k.motivo}`, usuario: nombreUsuario(k.usuario_id) },
    ),
    ...c.estados.slice(1).map<EventoHistorial>((e) => ({
      fecha: e.fecha,
      evento: "cambio_estado",
      detalle: `Estado: ${ETIQUETA_ESTADO[e.estado]}${e.observacion ? `. ${e.observacion}` : ""}${e.validado_por ? "" : " (asignado por el sistema según la nota)"}`,
      usuario: nombreUsuario(e.validado_por),
    })),
  ];
  return eventos.sort((a, b) => a.fecha.localeCompare(b.fecha));
}

function buscarCandidato(id: string) {
  const c = db.candidatos.find((x) => x.id === id);
  if (!c) throw new ApiRequestError("El candidato no existe.", "NOT_FOUND");
  return c;
}

const porNota = (a: CandidatoLista, b: CandidatoLista) =>
  (b.nota ?? 0) - (a.nota ?? 0) || a.creado_en.localeCompare(b.creado_en);

// ---------- API ----------
export const COOKIE_SESION = "immpetus_sesion";
const DOMINIO_PERMITIDO = "immpetus.co";

export async function obtenerSesion(): Promise<UsuarioAdmin> {
  await espera();
  return USUARIO_ACTUAL;
}

/** Simulado: con backend, se envía el id_token de Google a POST /api/auth/google y el backend pone la cookie. */
export async function iniciarSesion(correo: string = USUARIO_ACTUAL.correo): Promise<UsuarioAdmin> {
  await espera();
  if (!correo.toLowerCase().endsWith("@" + DOMINIO_PERMITIDO)) {
    throw new ApiRequestError("Solo pueden entrar cuentas @" + DOMINIO_PERMITIDO + ".", "FORBIDDEN");
  }
  const usuario = USUARIOS_MOCK.find((u) => u.correo === correo.toLowerCase());
  if (!usuario) throw new ApiRequestError("Tu cuenta no está registrada en el centro de mando. Pide acceso al líder de selección.", "FORBIDDEN");
  document.cookie = `${COOKIE_SESION}=simulada; path=/; max-age=28800; samesite=lax`;
  return usuario;
}

/** Simulado: con backend, POST /api/auth/logout. */
export async function cerrarSesion(): Promise<void> {
  document.cookie = `${COOKIE_SESION}=; path=/; max-age=0`;
}

export async function listarVacantesAdmin(): Promise<VacanteAdmin[]> {
  await espera();
  return structuredClone(db.vacantes);
}

export async function obtenerVacanteAdmin(id: string): Promise<VacanteAdmin> {
  await espera();
  const v = db.vacantes.find((x) => x.id === id);
  if (!v) throw new ApiRequestError("La vacante no existe.", "NOT_FOUND");
  return structuredClone(v);
}

const slugify = (s: string) =>
  s.toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "").replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

export async function crearVacante(input: VacanteInput): Promise<VacanteAdmin> {
  await espera();
  const iniciales = input.cargo.split(/\s+/).map((p) => p[0]).join("").slice(0, 3).toUpperCase();
  const nueva: VacanteAdmin = {
    ...input,
    id: crypto.randomUUID(),
    slug: slugify(input.cargo),
    codigo: `${iniciales}-${String(db.vacantes.length + 1).padStart(4, "0")}`,
    publicada_en: new Date().toISOString(),
  };
  db.vacantes.push(nueva);
  notificar();
  return structuredClone(nueva);
}

export async function actualizarVacante(id: string, cambios: Partial<VacanteInput>): Promise<VacanteAdmin> {
  await espera();
  const v = db.vacantes.find((x) => x.id === id);
  if (!v) throw new ApiRequestError("La vacante no existe.", "NOT_FOUND");
  Object.assign(v, cambios);
  notificar();
  return structuredClone(v);
}

export async function resumenVacante(id: string): Promise<ResumenVacante> {
  await espera();
  const cs = db.candidatos.filter((c) => c.vacante_id === id).map(aLista);
  return {
    recibidas: cs.length,
    nota_4_5: cs.filter((c) => (c.nota ?? 0) >= 4).length,
    reserva: cs.filter((c) => c.estado === "reserva").length,
    por_validar: cs.filter((c) => c.estado === "por_validar").length,
    entrevista: cs.filter((c) => c.estado === "entrevista").length,
  };
}

export async function listarCandidatos(filtro: { vacante_id?: string; estado?: EstadoCandidato } = {}): Promise<CandidatoLista[]> {
  await espera();
  return db.candidatos
    .map(aLista)
    .filter((c) => (!filtro.vacante_id || c.vacante_id === filtro.vacante_id) && (!filtro.estado || c.estado === filtro.estado))
    .sort(porNota);
}

export async function obtenerCandidato(id: string): Promise<CandidatoDetalle> {
  await espera();
  const c = buscarCandidato(id);
  return { ...aLista(c), resumen_ia: c.resumen_ia, matriz: structuredClone(c.matriz), historial: historial(c) };
}

export async function cambiarEstado(id: string, estado: EstadoCandidato, observacion?: string): Promise<CandidatoLista> {
  await espera();
  const c = buscarCandidato(id);
  const actual = estadoActual(c);
  if (!puedeTransitar(actual, estado)) {
    throw new ApiRequestError(`No se puede pasar de “${ETIQUETA_ESTADO[actual]}” a “${ETIQUETA_ESTADO[estado]}”.`, "CONFLICT");
  }
  c.estados.push({ estado, validado_por: USUARIO_ACTUAL.id, observacion: observacion?.trim() || null, fecha: new Date().toISOString() });
  notificar();
  return aLista(c);
}

/** Corrige la nota. Nunca cambia el estado (sección 5.4). */
export async function corregirNota(id: string, nota: number, motivo: string): Promise<CandidatoLista> {
  await espera();
  if (!Number.isInteger(nota) || nota < 1 || nota > 5) throw new ApiRequestError("La nota debe estar entre 1 y 5.", "VALIDATION_ERROR", "nota");
  if (motivo.trim().length < 5) throw new ApiRequestError("Explique el motivo de la corrección.", "VALIDATION_ERROR", "motivo");
  const c = buscarCandidato(id);
  c.calificaciones.push({ nota, origen: "analista", usuario_id: USUARIO_ACTUAL.id, motivo: motivo.trim(), fecha: new Date().toISOString() });
  notificar();
  return aLista(c);
}

export async function listarHabilidades(): Promise<Habilidad[]> {
  await espera();
  return [...HABILIDADES_MOCK].sort((a, b) => a.nombre.localeCompare(b.nombre));
}

export async function buscarReserva(filtro: { habilidades: string[]; cargo?: string }): Promise<CandidatoLista[]> {
  await espera();
  const cargo = filtro.cargo?.trim().toLowerCase();
  return db.candidatos
    .map(aLista)
    .filter((c) => c.estado === "reserva")
    .filter((c) => filtro.habilidades.every((h) => c.habilidades.some((x) => x.nombre === h)))
    .filter((c) => !cargo || db.vacantes.find((v) => v.id === c.vacante_id)?.cargo.toLowerCase().includes(cargo))
    .sort(porNota);
}

export async function listarCorreosSinAsignar(): Promise<CorreoSinAsignar[]> {
  await espera();
  return structuredClone(db.correos);
}

/** Crea el candidato desde el correo y dispara la calificación (sección 5.6). La nota aquí es simulada. */
export async function asignarCorreo(id: string, vacanteId: string): Promise<CandidatoLista> {
  await espera();
  const correo = db.correos.find((m) => m.id === id);
  if (!correo) throw new ApiRequestError("El correo ya fue asignado.", "NOT_FOUND");
  const ahora = new Date().toISOString();
  const nota = 3;
  const inicial = estadoInicialPorNota(nota);
  const nuevo: CandidatoRaw = {
    id: `c-${crypto.randomUUID().slice(0, 8)}`,
    vacante_id: vacanteId,
    nombre: `[Nombre extraído de ${correo.archivo_nombre}]`,
    correo: correo.remitente,
    celular: "",
    canal: "correo",
    creado_en: ahora,
    habilidades: [],
    resumen_ia: "[Resumen generado por la IA]",
    matriz: { formacion: "[Formación]", experiencia_anios: 0, sectores: [], justificacion: "[Justificación de la IA]" },
    calificaciones: [{ nota, origen: "ia", usuario_id: null, motivo: null, fecha: ahora }],
    estados: [
      { estado: "nuevo", validado_por: null, observacion: null, fecha: ahora },
      ...(inicial !== "nuevo" ? [{ estado: inicial, validado_por: null, observacion: null, fecha: ahora }] : []),
    ],
  };
  db.candidatos.push(nuevo);
  db.correos = db.correos.filter((m) => m.id !== id);
  notificar();
  return aLista(nuevo);
}

export async function enviarReporte(vacanteId: string, destinatarios: string[]): Promise<{ enviado: boolean }> {
  await espera();
  if (destinatarios.length === 0) throw new ApiRequestError("Agregue al menos un correo de destino.", "VALIDATION_ERROR", "destinatarios");
  void vacanteId;
  return { enviado: true };
}
