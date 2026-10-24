// Tabla de transiciones del contrato v0.2, sección 5.1. Debe coincidir con backend/app/services/estados.py.
import type { EstadoCandidato } from "@/types/api";

export const TRANSICIONES: Record<EstadoCandidato, EstadoCandidato[]> = {
  nuevo: ["entrevista", "reserva", "no_apto"],
  por_validar: ["entrevista", "reserva", "no_apto"],
  reserva: ["entrevista", "no_apto"],
  entrevista: ["reserva", "no_apto", "contratado"],
  no_apto: [],
  contratado: [],
};

export const ESTADOS_FINALES: EstadoCandidato[] = ["no_apto", "contratado"];

export const ETIQUETA_ESTADO: Record<EstadoCandidato, string> = {
  nuevo: "Nuevo",
  entrevista: "Entrevista",
  reserva: "Reserva",
  por_validar: "Por validar",
  no_apto: "No apto",
  contratado: "Contratado",
};

/** Texto del botón que lleva a cada estado. */
export const ACCION_ESTADO: Record<EstadoCandidato, string> = {
  nuevo: "Marcar como nuevo",
  entrevista: "Pasar a entrevista",
  reserva: "Enviar a reserva",
  por_validar: "Marcar por validar",
  no_apto: "Confirmar no apto",
  contratado: "Marcar contratado",
};

export function puedeTransitar(desde: EstadoCandidato, hacia: EstadoCandidato): boolean {
  return TRANSICIONES[desde].includes(hacia);
}

/** Mapeo nota → estado inicial (sección 5.3). Solo se aplica en la primera calificación de la IA. */
export function estadoInicialPorNota(nota: number): EstadoCandidato {
  if (nota >= 4) return "nuevo";
  if (nota === 3) return "reserva";
  return "por_validar";
}
