// Única puerta del frontend público a los datos (backend en NEXT_PUBLIC_API_URL).
import type {
  ApiError,
  Paginado,
  PostulacionCreada,
  VacanteDetalle,
  VacanteResumen,
} from "@/types/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
      body?.error?.message ??
        "No pudimos completar la solicitud. Intente de nuevo.",
      body?.error?.code ?? "UNKNOWN",
      body?.error?.field ?? undefined,
    );
  }
  return (await res.json()) as T;
}

export async function listarVacantes(): Promise<VacanteResumen[]> {
  const data = await request<Paginado<VacanteResumen>>(
    "/api/vacantes?page_size=100",
    {
      next: { revalidate: 60 },
    },
  );
  return data.items;
}

export async function obtenerVacante(
  slug: string,
): Promise<VacanteDetalle | null> {
  try {
    return await request<VacanteDetalle>(
      `/api/vacantes/${encodeURIComponent(slug)}`,
      {
        next: { revalidate: 60 },
      },
    );
  } catch (e) {
    if (e instanceof ApiRequestError && e.code === "NOT_FOUND") return null;
    throw e;
  }
}

export function enviarPostulacion(datos: FormData): Promise<PostulacionCreada> {
  return request<PostulacionCreada>("/api/postulaciones", {
    method: "POST",
    body: datos,
  });
}
