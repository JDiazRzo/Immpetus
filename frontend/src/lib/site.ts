export const SITE = {
  name: "Immpetus Soluciones",
  url: process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  contacto: {
    comercialCorreo: "contacto@immpetus.co",
    comercialTelefono: "+57 324 800 03 71",
    seleccionCorreo: "seleccion@immpetus.co",
    seleccionTelefono: "+57 319 277 90 78",
    seleccionNombre: "María Isabel",
    linkedin: "https://www.linkedin.com/company/immpetus-soluciones",
  },

  /** Tamaño máximo del PDF de la hoja de vida. [POR CONFIRMAR] con el equipo. */
  maxPdfMb: 5,
  /** Versión del texto de autorización de datos. Cambiarla si cambia el texto. */
  autorizacionVersion: "1.0",
} as const;

/** "+57 324 800 03 71" → "573248000371" (formato que piden wa.me y tel:) */
export const soloDigitos = (telefono: string) => telefono.replace(/\D/g, "");
