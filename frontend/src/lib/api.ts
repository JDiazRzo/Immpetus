// Única puerta del frontend a los datos. Mientras el backend no exista, responde con mocks.
// Para usar el backend real: NEXT_PUBLIC_USE_MOCKS=false y NEXT_PUBLIC_API_URL=<url>.
import { SLUGS_URGENTES, VACANTES_MOCK } from "@/mocks/vacantes";
import type {
  ApiError,
  Paginado,
  PostulacionCreada,
  VacanteDetalle,
  VacanteResumen,
} from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";

export class ApiRequestError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly field?: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as ApiError | null;
    throw new ApiRequestError(
      body?.error.message ?? "No pudimos completar la solicitud. Intente de nuevo.",
      body?.error.code ?? "UNKNOWN",
      body?.error.field,
    );
  }
  return (await res.json()) as T;
}

function aResumen(v: VacanteDetalle): VacanteResumen {
  return {
    id: v.id,
    slug: v.slug,
    cargo: v.cargo,
    ciudad: v.ciudad,
    modalidad: v.modalidad,
    modalidad_detalle: v.modalidad_detalle,
    jornada: v.jornada,
    salario_texto: v.salario_texto,
    urgente: SLUGS_URGENTES.has(v.slug),
    publicada_en: v.publicada_en,
  };
}

export async function listarVacantes(): Promise<VacanteResumen[]> {
  if (USE_MOCKS) return VACANTES_MOCK.map(aResumen);
  const data = await request<Paginado<VacanteResumen>>("/api/vacantes?page_size=100", {
    next: { revalidate: 60 },
  });
  return data.items;
}

export async function obtenerVacante(slug: string): Promise<VacanteDetalle | null> {
  if (USE_MOCKS) return VACANTES_MOCK.find((v) => v.slug === slug) ?? null;
  try {
    return await request<VacanteDetalle>(`/api/vacantes/${encodeURIComponent(slug)}`, {
      next: { revalidate: 60 },
    });
  } catch (e) {
    if (e instanceof ApiRequestError && e.code === "NOT_FOUND") return null;
    throw e;
  }
}

export async function enviarPostulacion(datos: FormData): Promise<PostulacionCreada> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 800));
    return { id: crypto.randomUUID(), estado: "nuevo", mensaje: "Postulación enviada." };
  }
  return request<PostulacionCreada>("/api/postulaciones", { method: "POST", body: datos });
}
