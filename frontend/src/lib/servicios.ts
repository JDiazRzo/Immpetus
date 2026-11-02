import type { ServicioContacto } from "@/types/api";

export type LineaServicio = {
  id: ServicioContacto;
  numero: string;
  nombre: string;
  resumen: string;
  destacado: { titulo: string; texto: string };
  items: ReadonlyArray<{ titulo: string; texto: string }>;
};

export const LINEAS_SERVICIO: ReadonlyArray<LineaServicio> = [
  {
    id: "adquisicion_talento",
    numero: "01",
    nombre: "Adquisición de Talento",
    resumen: "Búsqueda estratégica de talento que genera resultados. Conectamos organizaciones con los perfiles más calificados.",
    destacado: {
      titulo: "Búsqueda especializada a la medida",
      texto: "Desde talento operativo hasta ejecutivos C-Level. Metodologías rigurosas de entrevista por competencias, pruebas técnicas y assessment cultural para garantizar el fit perfecto.",
    },
    items: [
      { titulo: "Talento Core", texto: "Personal asistencial y operativo para el soporte y funcionalidad diaria de su empresa." },
      { titulo: "Talento Masivo", texto: "Gestión de altos volúmenes de contratación en tiempos cortos y bajo costo unitario." },
      { titulo: "Talento Pro", texto: "Profesionales de nivel táctico y mandos intermedios, clave para la continuidad del negocio." },
      { titulo: "Executive Search — Headhunting", texto: "Búsqueda directa de cargos de alta dirección y estratégicos con confidencialidad y rapidez." },
      { titulo: "Talento Growth & Tech", texto: "El mejor talento de LATAM en IT, Marketing y Estrategia para escalar su negocio digital." },
      { titulo: "Talento Edu & Sales 360", texto: "Talento certificado para el sector educativo y fuerza comercial de alto rendimiento." },
    ],
  },
  {
    id: "talento_bpo",
    numero: "02",
    nombre: "Talento BPO",
    resumen: "Servicios transaccionales y de blindaje legal para que sus operaciones se enfoquen en la estrategia del negocio.",
    destacado: {
      titulo: "Blindaje legal y operativo total",
      texto: "Asumimos la carga administrativa de su capital humano. Cumplimiento normativo colombiano y LATAM con respaldo jurídico integral en cada operación.",
    },
    items: [
      { titulo: "Administración y Compensación Estratégica", texto: "Gestión integral de nómina de empresas colombianas con RR. HH. local y cumplimiento normativo." },
      { titulo: "EOR — Employer of Record", texto: "Actuamos como empleador legal en LATAM para empresas internacionales con estructura legal en Colombia." },
      { titulo: "Servicios Temporales — Staffing", texto: "Suministro ágil de personal calificado para proyectos específicos con total respaldo jurídico." },
    ],
  },
  {
    id: "gestion_estrategica",
    numero: "03",
    nombre: "Gestión Estratégica del Talento",
    resumen: "Metodologías para desarrollar, fortalecer y retener el mejor talento, consolidando su cultura organizacional.",
    destacado: {
      titulo: "Desarrollamos el talento que ya tiene",
      texto: "Desde el primer día (onboarding) hasta la desvinculación responsable. Sistemas de evaluación, compensación y bienestar que convierten colaboradores en activos estratégicos.",
    },
    items: [
      { titulo: "Onboarding Estratégico", texto: "Planes de 30, 60 y 90 días para reducir la ansiedad y acelerar la curva de aprendizaje inicial." },
      { titulo: "Gestión del Desempeño y KPI", texto: "Sistemas de evaluación y métricas de rendimiento para medir el impacto real del talento." },
      { titulo: "Compensación y Beneficios", texto: "Escalas salariales y modelos de incentivos basados en benchmarking de mercado." },
      { titulo: "Cultura y Bienestar 360°", texto: "Mapa de experiencia del empleado, estrategias de clima laboral y guías de desconexión." },
      { titulo: "Offboarding y Marca Empleadora", texto: "Desvinculación responsable con entrevistas estratégicas para proteger la reputación institucional." },
    ],
  },
  {
    id: "formacion_liderazgo",
    numero: "04",
    nombre: "Formación, Liderazgo y Alto Desempeño",
    resumen: "Transformamos el conocimiento en un activo estratégico para potenciar la competitividad organizacional.",
    destacado: {
      titulo: "Líderes que transforman organizaciones",
      texto: "Programas a la medida que combinan power skills con competencias técnicas. Coaching ejecutivo personalizado para líderes con foco en resultados extraordinarios.",
    },
    items: [
      { titulo: "Liderazgo y Alto Desempeño", texto: "Programas para fortalecer la dirección de personas hacia resultados extraordinarios y cohesión grupal." },
      { titulo: "Coaching Ejecutivo", texto: "Acompañamiento personalizado para líderes y mandos medios en desarrollo estratégico." },
      { titulo: "Entrenamiento Integral (blando y técnico)", texto: "Formación que equilibra power skills con competencias técnicas específicas para la operación." },
      { titulo: "Planes de Carrera y Desarrollo Individual", texto: "Rutas de crecimiento profesional para retener y proyectar el talento clave." },
      { titulo: "Diagnóstico y Evaluación de Impacto", texto: "Identificación de brechas y medición del impacto de la formación en la productividad." },
    ],
  },
  {
    id: "procesos",
    numero: "05",
    nombre: "Diseño y Mejoramiento de Procesos",
    resumen: "Transformamos la operatividad en eficiencia mediante metodologías ágiles centradas en la excelencia del servicio.",
    destacado: {
      titulo: "Operatividad de clase mundial",
      texto: "Six Sigma, PHVA y Kaizen para eliminar cuellos de botella. Arquitecturas organizacionales eficientes con Bizagi, Visio y estándares ISO para la continuidad del negocio.",
    },
    items: [
      { titulo: "Diseño de Procesos", texto: "Diseño, rediseño y optimización de flujos con Bizagi y Visio. Six Sigma, PHVA y Kaizen." },
      { titulo: "Arquitectura y Diseño Organizacional", texto: "Definición de arquitecturas eficientes, valoración de cargos y rediseño de roles y responsabilidades." },
      { titulo: "Implementación y Gestión de Calidad", texto: "Sistemas de gestión ISO, mitigación de riesgos operativos y monitoreo de indicadores de gestión." },
      { titulo: "Gestión del Cambio y Cultura", texto: "Acompañamiento estratégico para asegurar la adopción y adherencia del talento en cada transformación." },
    ],
  },
];
