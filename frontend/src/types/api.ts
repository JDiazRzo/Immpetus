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

// ---------- Centro de mando (/api/admin) ----------

export type Rol = "analista" | "lider" | "gerencia";
export type Canal = "web" | "correo";

export type UsuarioAdmin = {
  id: string;
  correo: string;
  nombre: string;
  rol: Rol;
};

export type CriterioAdmin = {
  habilidad_id: string;
  habilidad: string;
  obligatoria: boolean;
  peso: number;
};

export type VacanteAdmin = Omit<VacanteDetalle, "criterios"> & {
  codigo: string;
  cliente: string | null;
  urgente: boolean;
  activa: boolean;
  criterios: CriterioAdmin[];
};

export type VacanteInput = Omit<VacanteAdmin, "id" | "slug" | "publicada_en" | "codigo">;

export type ResumenVacante = {
  recibidas: number;
  nota_4_5: number;
  reserva: number;
  por_validar: number;
  entrevista: number;
};

export type HabilidadCandidato = {
  nombre: string;
  coincide: boolean;
};

export type CandidatoLista = {
  id: string;
  vacante_id: string;
  nombre: string;
  correo: string;
  celular: string | null;
  canal: Canal;
  drive_url: string | null;
  archivo_nombre: string | null;
  nota: number | null;
  nota_validada: boolean;
  validada_por: string | null;
  estado: EstadoCandidato;
  habilidades: HabilidadCandidato[];
  creado_en: string;
};

export type TipoEvento =
  | "postulacion_recibida"
  | "hv_guardada"
  | "calificacion_ia"
  | "calificacion_analista"
  | "cambio_estado";

export type EventoHistorial = {
  fecha: string;
  evento: TipoEvento;
  detalle: string;
  usuario: string | null;
};

export type MatrizIA = {
  formacion: string;
  experiencia_anios: number;
  sectores: string[];
  justificacion: string;
};

export type CandidatoDetalle = CandidatoLista & {
  resumen_ia: string | null;
  matriz: MatrizIA | null;
  historial: EventoHistorial[];
};

export type Habilidad = {
  id: string;
  nombre: string;
  categoria: "tecnica" | "blanda" | "idioma" | "herramienta" | "certificacion";
};

export type CorreoSinAsignar = {
  id: string;
  remitente: string;
  asunto: string | null;
  archivo_nombre: string;
  recibido_en: string;
};
