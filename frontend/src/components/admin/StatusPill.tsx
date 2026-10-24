import { ETIQUETA_ESTADO } from "@/lib/estados";
import { cn } from "@/lib/cn";
import type { EstadoCandidato } from "@/types/api";

const ESTILO: Record<EstadoCandidato, string> = {
  nuevo: "bg-[#ECEEF4] text-[#343861]",
  entrevista: "bg-[#E3F2EA] text-[#0F5E38]",
  reserva: "bg-[#E4ECF8] text-[#234A8A]",
  por_validar: "bg-[#FBE7D6] text-[#7F3409]",
  no_apto: "bg-[#EDEDED] text-[#4A4A4A]",
  contratado: "bg-ok text-white",
};

export function StatusPill({ estado }: { estado: EstadoCandidato }) {
  return (
    <span className={cn("inline-block whitespace-nowrap rounded-full px-2.5 py-1 text-[13px] font-bold", ESTILO[estado])}>
      {ETIQUETA_ESTADO[estado]}
    </span>
  );
}
