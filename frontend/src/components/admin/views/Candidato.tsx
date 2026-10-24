"use client";

import Link from "next/link";
import { useId, useState } from "react";
import { cambiarEstado, corregirNota, obtenerCandidato, obtenerVacanteAdmin } from "@/lib/admin-api";
import { ACCION_ESTADO, ESTADOS_FINALES, TRANSICIONES } from "@/lib/estados";
import { cn } from "@/lib/cn";
import { useAdmin } from "@/lib/use-admin";
import type { CandidatoDetalle, EstadoCandidato } from "@/types/api";
import { AuditTrail } from "../AuditTrail";
import { MatchChip } from "../MatchChip";
import { Estado, Panel } from "../Panel";
import { PageTitle } from "../PageTitle";
import { ScoreMeter } from "../ScoreMeter";
import { StatusPill } from "../StatusPill";

export function Candidato({ id }: { id: string }) {
  const cand = useAdmin(() => obtenerCandidato(id), [id]);
  const vacanteId = cand.datos?.vacante_id;
  const vacante = useAdmin(() => (vacanteId ? obtenerVacanteAdmin(vacanteId) : Promise.resolve(null)), [vacanteId]);

  if (cand.estado !== "listo") return <Estado cargando={cand.estado === "cargando"} error={cand.error} />;
  const c = cand.datos;
  const v = vacante.datos;

  return (
    <>
      <PageTitle
        antetitulo={v ? <Link href={`/admin/vacantes/${v.id}`} className="font-semibold text-action">{v.cargo}</Link> : "…"}
        titulo={c.nombre}
        acciones={<StatusPill estado={c.estado} />}
      />

      <div className="flex flex-wrap items-start gap-6">
        <div className="flex min-w-0 flex-[999_1_560px] flex-col gap-6">
          <Panel titulo="Evaluación">
            <div className="flex flex-col gap-5 p-5">
              <ScoreMeter nota={c.nota} validada={c.nota_validada} validadaPor={c.validada_por} />
              {c.resumen_ia && (
                <div>
                  <h3 className="text-sm font-semibold text-ink-soft">Resumen de la IA</h3>
                  <p className="mt-1 max-w-[70ch] leading-relaxed">{c.resumen_ia}</p>
                </div>
              )}
              <div>
                <h3 className="text-sm font-semibold text-ink-soft">Habilidades (resaltado: coincide con el cargo)</h3>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {c.habilidades.length ? c.habilidades.map((h) => <MatchChip key={h.nombre} {...h} />) : <span className="text-sm text-ink-soft">Sin habilidades detectadas</span>}
                </div>
              </div>
              {c.matriz && (
                <dl className="grid gap-4 border-t border-line pt-4 sm:grid-cols-3">
                  <div><dt className="text-sm text-ink-soft">Formación</dt><dd className="font-semibold">{c.matriz.formacion}</dd></div>
                  <div><dt className="text-sm text-ink-soft">Experiencia</dt><dd className="font-semibold tabular-nums">{c.matriz.experiencia_anios} años</dd></div>
                  <div><dt className="text-sm text-ink-soft">Sectores</dt><dd className="font-semibold">{c.matriz.sectores.join(", ") || "–"}</dd></div>
                </dl>
              )}
            </div>
          </Panel>

          <Panel titulo="Historial">
            <div className="px-5 py-2"><AuditTrail eventos={c.historial} /></div>
          </Panel>
        </div>

        <div className="flex w-full min-w-0 flex-[1_1_340px] flex-col gap-6">
          <Panel titulo="Contacto">
            <dl className="flex flex-col gap-3 p-5 text-[15px]">
              <div><dt className="text-sm text-ink-soft">Correo</dt><dd><a href={`mailto:${c.correo}`} className="text-action">{c.correo}</a></dd></div>
              <div><dt className="text-sm text-ink-soft">Celular</dt><dd>{c.celular || "–"}</dd></div>
              <div><dt className="text-sm text-ink-soft">Hoja de vida</dt><dd><a href={c.drive_url ?? "#"} className="break-all text-action">{c.archivo_nombre}</a></dd></div>
            </dl>
          </Panel>
          <AccionesEstado candidato={c} />
          <CorregirNota candidato={c} />
        </div>
      </div>
    </>
  );
}

function AccionesEstado({ candidato }: { candidato: CandidatoDetalle }) {
  const uid = useId();
  const [pendiente, setPendiente] = useState<EstadoCandidato | null>(null);
  const [observacion, setObservacion] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const opciones = TRANSICIONES[candidato.estado];

  async function confirmar(estado: EstadoCandidato) {
    setEnviando(true);
    setError(null);
    try {
      await cambiarEstado(candidato.id, estado, observacion);
      setPendiente(null);
      setObservacion("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cambiar el estado.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Panel titulo="Decisión">
      <div className="flex flex-col gap-4 p-5">
        {candidato.estado === "por_validar" && (
          <p className="rounded-chip bg-[#FFF9EC] px-3 py-2 text-sm text-[#7F3409]">
            La IA sugirió una nota baja. Revise la hoja de vida antes de decidir: el sistema nunca descarta por sí solo.
          </p>
        )}
        {opciones.length === 0 ? (
          <p className="text-sm text-ink-soft">Este estado es final. Si hubo un error, lo resuelve el líder de RR. HH.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {opciones.map((estado) => {
              const final = ESTADOS_FINALES.includes(estado);
              return (
                <button
                  key={estado}
                  type="button"
                  onClick={() => (final ? setPendiente(estado) : confirmar(estado))}
                  disabled={enviando}
                  className={cn(
                    "min-h-11 rounded-chip px-4 text-left font-semibold disabled:opacity-60",
                    estado === "entrevista" ? "bg-action text-white" : estado === "no_apto" ? "border border-review text-[#7F3409]" : "border border-line-strong",
                  )}
                >
                  {ACCION_ESTADO[estado]}
                </button>
              );
            })}
          </div>
        )}

        {pendiente && (
          <div className="flex flex-col gap-3 rounded-chip border border-line p-4">
            <p className="font-semibold">“{ACCION_ESTADO[pendiente]}” es una decisión final. ¿Confirma?</p>
            <label htmlFor={`${uid}-obs`} className="flex flex-col gap-1.5 text-sm font-semibold">
              Observación (recomendada)
              <textarea id={`${uid}-obs`} rows={3} value={observacion} onChange={(e) => setObservacion(e.target.value)} className="rounded-chip border border-line-strong p-2.5 text-base font-normal" />
            </label>
            <div className="flex gap-2">
              <button type="button" onClick={() => confirmar(pendiente)} disabled={enviando} className="min-h-11 rounded-chip bg-ink px-4 font-bold text-white disabled:opacity-60">
                Sí, {ACCION_ESTADO[pendiente].toLowerCase()}
              </button>
              <button type="button" onClick={() => setPendiente(null)} className="min-h-11 rounded-chip border border-line-strong px-4 font-semibold">
                Cancelar
              </button>
            </div>
          </div>
        )}
        {error && <p role="alert" className="text-sm font-semibold text-review">{error}</p>}
      </div>
    </Panel>
  );
}

function CorregirNota({ candidato }: { candidato: CandidatoDetalle }) {
  const uid = useId();
  const [abierto, setAbierto] = useState(false);
  const [nota, setNota] = useState(candidato.nota ?? 3);
  const [motivo, setMotivo] = useState("");
  const [mensaje, setMensaje] = useState<{ tipo: "ok" | "error"; texto: string } | null>(null);

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    try {
      await corregirNota(candidato.id, nota, motivo);
      setMensaje({ tipo: "ok", texto: "Nota corregida. El estado no cambia: si quiere moverlo, use Decisión." });
      setMotivo("");
      setAbierto(false);
    } catch (err) {
      setMensaje({ tipo: "error", texto: err instanceof Error ? err.message : "No se pudo corregir la nota." });
    }
  }

  return (
    <Panel titulo="Nota">
      <div className="flex flex-col gap-3 p-5">
        {!abierto ? (
          <button type="button" onClick={() => setAbierto(true)} className="min-h-11 rounded-chip border border-line-strong px-4 text-left font-semibold">
            Corregir nota
          </button>
        ) : (
          <form onSubmit={guardar} className="flex flex-col gap-3">
            <fieldset className="flex flex-col gap-2">
              <legend className="text-sm font-semibold">Nueva nota</legend>
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <label key={n} className={cn("flex size-11 cursor-pointer items-center justify-center rounded-chip border font-bold", nota === n ? "border-ink bg-ink text-white" : "border-line-strong")}>
                    <input type="radio" name={`${uid}-nota`} value={n} checked={nota === n} onChange={() => setNota(n)} className="sr-only" />
                    {n}
                  </label>
                ))}
              </div>
            </fieldset>
            <label htmlFor={`${uid}-motivo`} className="flex flex-col gap-1.5 text-sm font-semibold">
              Motivo (obligatorio)
              <textarea id={`${uid}-motivo`} rows={3} value={motivo} onChange={(e) => setMotivo(e.target.value)} className="rounded-chip border border-line-strong p-2.5 text-base font-normal" />
            </label>
            <div className="flex gap-2">
              <button type="submit" className="min-h-11 rounded-chip bg-action px-4 font-bold text-white">Guardar nota</button>
              <button type="button" onClick={() => setAbierto(false)} className="min-h-11 rounded-chip border border-line-strong px-4 font-semibold">Cancelar</button>
            </div>
          </form>
        )}
        {mensaje && (
          <p role={mensaje.tipo === "error" ? "alert" : "status"} className={cn("text-sm font-semibold", mensaje.tipo === "ok" ? "text-ok" : "text-review")}>
            {mensaje.texto}
          </p>
        )}
      </div>
    </Panel>
  );
}
