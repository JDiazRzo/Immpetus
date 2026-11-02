import { SITE } from "@/lib/site";

const soloDigitos = (tel: string) => tel.replace(/\D/g, "");

const ICONOS = {
  whatsapp:
    "M20 11.5a8.5 8.5 0 0 1-12.6 7.4L3 20l1.2-4.3A8.5 8.5 0 1 1 20 11.5zM8.5 8.5c.3 2.8 2.2 5 5 6l1.2-1.2 2 .9-.4 1.6c-3.8.3-8-3.7-8-7.6l1.6-.5.9 2z",
  telefono:
    "M5 3h4l2 5-2.5 1.5a11 11 0 0 0 6 6L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 5a2 2 0 0 1 2-2z",
  linkedin:
    "M4 9h4v11H4zM6 4a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM10 9h4v1.6c.6-1 1.9-1.8 3.4-1.8 3 0 3.6 2 3.6 4.6V20h-4v-5.6c0-1.3 0-3-1.8-3s-2.2 1.4-2.2 2.9V20h-4z",
  externo:
    "M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5",
} as const;

function Svg({ d, className = "size-5" }: { d: string; className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d={d} />
    </svg>
  );
}

const TELEFONOS = [
  { numero: SITE.contacto.comercialTelefono, area: "Comercial" },
  { numero: SITE.contacto.seleccionTelefono, area: "Selección · María Isabel" },
];

const tituloBloque = "text-sm font-bold text-ink";

export function ContactoCanales() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h3 className={tituloBloque}>Correo institucional</h3>
        <a
          href={`mailto:${SITE.contacto.comercialCorreo}`}
          className="w-fit font-semibold text-action hover:underline"
        >
          {SITE.contacto.comercialCorreo}
        </a>
        <a
          href={`mailto:${SITE.contacto.seleccionCorreo}`}
          className="w-fit font-semibold text-action hover:underline"
        >
          {SITE.contacto.seleccionCorreo}
        </a>
      </div>

      <div className="flex flex-col gap-2">
        <h3 className={tituloBloque}>WhatsApp y teléfono</h3>
        <ul className="flex flex-col gap-2">
          {TELEFONOS.map((t) => (
            <li key={t.numero} className="flex items-center gap-2">
              {/* El número completo abre WhatsApp */}
              <a
                href={`https://wa.me/${soloDigitos(t.numero)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="group flex min-h-11 flex-1 items-center gap-3 rounded-chip px-2 -mx-2 hover:bg-brand-tint"
              >
                <span className="text-action">
                  <Svg d={ICONOS.whatsapp} />
                </span>
                <span className="flex flex-col">
                  <span className="font-semibold tabular-nums group-hover:text-action">
                    {t.numero}
                  </span>
                  <span className="text-sm text-ink-soft">{t.area}</span>
                </span>
                <span className="sr-only">(abre WhatsApp en otra pestaña)</span>
              </a>
              <a
                href={`tel:+${soloDigitos(t.numero)}`}
                className="grid size-11 shrink-0 place-items-center rounded-chip text-ink-soft hover:bg-brand-tint hover:text-action"
                aria-label={`Llamar a ${t.area}`}
                title="Llamar"
              >
                <Svg d={ICONOS.telefono} />
              </a>
            </li>
          ))}
        </ul>
      </div>

      <a
        href={SITE.contacto.linkedin}
        target="_blank"
        rel="noopener noreferrer"
        className="group flex items-center gap-4 rounded-panel border border-line bg-surface p-4 hover:border-action"
      >
        <span className="grid size-11 shrink-0 place-items-center rounded-chip bg-[#0A66C2] text-white">
          <Svg d={ICONOS.linkedin} />
        </span>
        <span className="flex min-w-0 flex-1 flex-col">
          <span className="font-bold group-hover:text-action">
            LinkedIn · Immpetus Soluciones
          </span>
          <span className="text-sm text-ink-soft">
            +6.000 seguidores · Novedades y vacantes
          </span>
        </span>
        <span className="text-ink-soft group-hover:text-action">
          <Svg d={ICONOS.externo} className="size-4" />
        </span>
        <span className="sr-only">(se abre en otra pestaña)</span>
      </a>
    </div>
  );
}
