import { cn } from "@/lib/cn";

const COLOR = (nota: number) => (nota >= 4 ? "bg-ok" : nota === 3 ? "bg-reserve" : "bg-review");

type Props = { nota: number | null; validada: boolean; validadaPor: string | null; compacto?: boolean };

/** Nota Likert en 5 segmentos. Siempre muestra el número: el color no es la única señal. */
export function ScoreMeter({ nota, validada, validadaPor, compacto }: Props) {
  if (nota === null) return <span className="text-sm text-ink-soft">Sin calificar</span>;
  return (
    <div className="flex flex-col gap-1">
      <span className="flex items-center gap-2" role="img" aria-label={`Nota ${nota} de 5`}>
        <span aria-hidden="true" className="flex gap-[3px]">
          {[1, 2, 3, 4, 5].map((i) => (
            <span key={i} className={cn("h-[18px] w-2.5 rounded-[2px]", i <= nota ? COLOR(nota) : "bg-line")} />
          ))}
        </span>
        <strong className="tabular-nums">{nota}</strong>
      </span>
      {!compacto && (
        <span className="text-xs text-ink-soft">{validada ? `Validada por ${validadaPor ?? "RR. HH."}` : "Sugerida por IA"}</span>
      )}
    </div>
  );
}
