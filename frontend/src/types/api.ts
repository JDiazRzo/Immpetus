// Tipos copiados de docs/CONTRATO_API.md. Si el contrato cambia, se actualizan aquí.

export type Modalidad = "presencial" | "hibrido" | "remoto";

export type EstadoCandidato =
  | "nuevo"
  | "entrevista"
  | "reserva"
  | "por_validar"
  | "no_apto"
  | "contratado";

export type Paginado<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type VacanteResumen = {
  id: string;
  slug: string;
  cargo: string;
  ciudad: string;
  modalidad: Modalidad;
  modalidad_detalle: string | null;
  jornada: string | null;
  salario_texto: string | null;
  urgente: boolean;
  publicada_en: string;
};

export type CriterioVacante = {
  habilidad: string;
  obligatoria: boolean;
};

export type VacanteDetalle = Omit<VacanteResumen, "urgente" | "publicada_en"> & {
  descripcion: string | null;
  responsabilidades: string[];
  criterios: CriterioVacante[];
  publicada_en: string;
};

export type PostulacionCreada = {
  id: string;
  estado: EstadoCandidato;
  mensaje: string;
};

export type ApiError = {
  error: {
    code: string;
    message: string;
    field?: string;
  };
};
