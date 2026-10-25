// Centro de mando contra el backend real (contrato v0.3).
// Las llamadas van a /api/... del mismo dominio; next.config.ts las reenvía al backend,
// así la cookie httpOnly de sesión viaja sola.
import type {
  ApiError,
  CandidatoDetalle,
  CandidatoLista,
  CorreoSinAsignar,
  EstadoCandidato,
  Habilidad,
  Paginado,
  ResumenVacante,
  UsuarioAdmin,
  VacanteAdmin,
  VacanteInput,
} from "@/types/api";
import { notificar } from "./admin-eventos";
import { ApiRequestError } from "./api";

const TODO = "page_size=100";

async function pedir<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(ruta, {
    ...init,
    credentials: "include",
    headers: init.body ? { "Content-Type": "application/json", ...init.headers } : init.headers,
  });

  if (res.status === 401 && !ruta.startsWith("/api/auth/")) {
    const actual = window.location.pathname + window.location.search;
    window.location.assign(`/admin/login?next=${encodeURIComponent(actual)}`);
  }
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as ApiError | null;
    throw new ApiRequestError(
      body?.error?.message ?? "No pudimos completar la solicitud. Intente de nuevo.",
      body?.error?.code ?? "UNKNOWN",
      body?.error?.field ?? undefined,
    );
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

const json = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

async function mutar<T>(ruta: string, init: RequestInit): Promise<T> {
  const r = await pedir<T>(ruta, init);
  notificar();
  return r;
}

// ---------- Sesión ----------
export const obtenerSesion = () => pedir<UsuarioAdmin>("/api/admin/me");

export const iniciarSesion = (idToken: string) => pedir<UsuarioAdmin>("/api/auth/google", json({ id_token: idToken }));

export async function cerrarSesion(): Promise<void> {
  await pedir<void>("/api/auth/logout", { method: "POST" });
}

// ---------- Vacantes ----------
export async function listarVacantesAdmin(): Promise<VacanteAdmin[]> {
  return (await pedir<Paginado<VacanteAdmin>>(`/api/admin/vacantes?${TODO}`)).items;
}

export const obtenerVacanteAdmin = (id: string) => pedir<VacanteAdmin>(`/api/admin/vacantes/${id}`);

export const crearVacante = (input: VacanteInput) => mutar<VacanteAdmin>("/api/admin/vacantes", json(input));

export const actualizarVacante = (id: string, cambios: Partial<VacanteInput>) =>
  mutar<VacanteAdmin>(`/api/admin/vacantes/${id}`, { method: "PATCH", body: JSON.stringify(cambios) });

export const resumenVacante = (id: string) => pedir<ResumenVacante>(`/api/admin/vacantes/${id}/resumen`);

// ---------- Candidatos ----------
async function candidatosDeVacante(vacanteId: string, estado?: EstadoCandidato): Promise<CandidatoLista[]> {
  const q = new URLSearchParams({ page_size: "100", orden: "nota_desc" });
  if (estado) q.set("estado", estado);
  const data = await pedir<Paginado<CandidatoLista>>(`/api/admin/vacantes/${vacanteId}/candidatos?${q}`);
  return data.items.map((c) => ({ ...c, vacante_id: c.vacante_id ?? vacanteId }));
}

/** Sin vacante_id recorre todas las vacantes (lo usa la bandeja "Por validar"). */
export async function listarCandidatos(filtro: { vacante_id?: string; estado?: EstadoCandidato } = {}): Promise<CandidatoLista[]> {
  if (filtro.vacante_id) return candidatosDeVacante(filtro.vacante_id, filtro.estado);
  const vacantes = await listarVacantesAdmin();
  const listas = await Promise.all(vacantes.map((v) => candidatosDeVacante(v.id, filtro.estado)));
  return listas.flat().sort((a, b) => (b.nota ?? 0) - (a.nota ?? 0));
}

export const obtenerCandidato = (id: string) => pedir<CandidatoDetalle>(`/api/admin/candidatos/${id}`);

export const cambiarEstado = (id: string, estado: EstadoCandidato, observacion?: string) =>
  mutar<CandidatoLista>(`/api/admin/candidatos/${id}/estado`, json({ estado, observacion: observacion?.trim() || null }));

/** Corrige la nota. Nunca cambia el estado (sección 5.4). */
export const corregirNota = (id: string, nota: number, motivo: string) =>
  mutar<CandidatoLista>(`/api/admin/candidatos/${id}/calificacion`, json({ nota, motivo: motivo.trim() }));

// ---------- Habilidades y reserva ----------
export async function listarHabilidades(): Promise<Habilidad[]> {
  const hs = await pedir<Habilidad[]>("/api/admin/habilidades");
  return [...hs].sort((a, b) => a.nombre.localeCompare(b.nombre));
}

/** La pantalla filtra por nombre de habilidad; el backend recibe ids. */
export async function buscarReserva(filtro: { habilidades: string[]; cargo?: string }): Promise<CandidatoLista[]> {
  const q = new URLSearchParams();
  if (filtro.habilidades.length > 0) {
    const catalogo = await listarHabilidades();
    for (const nombre of filtro.habilidades) {
      const h = catalogo.find((x) => x.nombre === nombre);
      if (h) q.append("habilidad_id", h.id);
    }
  }
  if (filtro.cargo?.trim()) q.set("cargo", filtro.cargo.trim());
  const data = await pedir<Paginado<CandidatoLista> | CandidatoLista[]>(`/api/admin/reserva?${q}`);
  return Array.isArray(data) ? data : data.items;
}

// ---------- Correos sin asignar ----------
export async function listarCorreosSinAsignar(): Promise<CorreoSinAsignar[]> {
  const data = await pedir<Paginado<CorreoSinAsignar> | CorreoSinAsignar[]>(`/api/admin/correos-sin-asignar?${TODO}`);
  return Array.isArray(data) ? data : data.items;
}

export const asignarCorreo = (id: string, vacanteId: string) =>
  mutar<CandidatoLista>(`/api/admin/correos-sin-asignar/${id}/asignar`, json({ vacante_id: vacanteId }));

// ---------- Reporte ----------
export const enviarReporte = (vacanteId: string, destinatarios: string[]) =>
  pedir<{ enviado: boolean }>(`/api/admin/vacantes/${vacanteId}/reporte`, json({ destinatarios }));
