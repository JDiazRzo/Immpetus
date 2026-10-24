"use client";

import { useRouter } from "next/navigation";
import { useId, useState } from "react";
import { actualizarVacante, crearVacante, listarHabilidades, obtenerVacanteAdmin } from "@/lib/admin-api";
import { useAdmin } from "@/lib/use-admin";
import type { CriterioAdmin, Modalidad, VacanteAdmin, VacanteInput } from "@/types/api";
import { Estado, Panel } from "../Panel";
import { PageTitle } from "../PageTitle";

const VACIA: VacanteInput = {
  cargo: "",
  cliente: "",
  ciudad: "Bogotá",
  modalidad: "presencial",
  modalidad_detalle: "",
  jornada: "Tiempo completo",
  salario_texto: "",
  descripcion: "",
  responsabilidades: [],
  criterios: [],
  urgente: false,
  activa: false,
};

const input = "min-h-11 w-full rounded-chip border border-line-strong bg-surface px-3 text-base";

export function VacancyFormPage({ id }: { id?: string }) {
  const existente = useAdmin(() => (id ? obtenerVacanteAdmin(id) : Promise.resolve(null)), [id]);
  if (existente.estado !== "listo") return <Estado cargando={existente.estado === "cargando"} error={existente.error} />;
  return <VacancyForm inicial={existente.datos} />;
}

function VacancyForm({ inicial }: { inicial: VacanteAdmin | null }) {
  const router = useRouter();
  const uid = useId();
  const habilidades = useAdmin(listarHabilidades, []);
  const [datos, setDatos] = useState<VacanteInput>(inicial ?? VACIA);
  const [responsabilidades, setResponsabilidades] = useState((inicial?.responsabilidades ?? []).join("\n"));
  const [errores, setErrores] = useState<string[]>([]);
  const [guardando, setGuardando] = useState(false);

  const set = <K extends keyof VacanteInput>(k: K, v: VacanteInput[K]) => setDatos((d) => ({ ...d, [k]: v }));
  const criterio = (habId: string) => datos.criterios.find((c) => c.habilidad_id === habId);

  function alternarCriterio(habId: string, nombre: string) {
    set(
      "criterios",
      criterio(habId)
        ? datos.criterios.filter((c) => c.habilidad_id !== habId)
        : [...datos.criterios, { habilidad_id: habId, habilidad: nombre, obligatoria: false, peso: 1 }],
    );
  }

  function editarCriterio(habId: string, cambios: Partial<CriterioAdmin>) {
    set("criterios", datos.criterios.map((c) => (c.habilidad_id === habId ? { ...c, ...cambios } : c)));
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    const errs: string[] = [];
    if (datos.cargo.trim().length < 3) errs.push("Escriba el nombre del cargo.");
    if (!datos.ciudad.trim()) errs.push("Escriba la ciudad.");
    if (datos.criterios.length === 0) errs.push("Elija al menos un criterio de calificación.");
    setErrores(errs);
    if (errs.length) return;

    const payload: VacanteInput = {
      ...datos,
      cliente: datos.cliente?.trim() || null,
      modalidad_detalle: datos.modalidad_detalle?.trim() || null,
      salario_texto: datos.salario_texto?.trim() || null,
      descripcion: datos.descripcion?.trim() || null,
      responsabilidades: responsabilidades.split("\n").map((r) => r.trim()).filter(Boolean),
    };
    setGuardando(true);
    const v = inicial ? await actualizarVacante(inicial.id, payload) : await crearVacante(payload);
    router.push(`/admin/vacantes/${v.id}`);
  }

  const campo = (k: keyof VacanteInput, etiqueta: string, props: React.InputHTMLAttributes<HTMLInputElement> = {}) => (
    <label htmlFor={`${uid}-${k}`} className="flex flex-col gap-1.5 text-sm font-semibold">
      {etiqueta}
      <input
        id={`${uid}-${k}`}
        className={`${input} font-normal`}
        value={String(datos[k] ?? "")}
        onChange={(e) => set(k, e.target.value as never)}
        {...props}
      />
    </label>
  );

  return (
    <>
      <PageTitle antetitulo={inicial?.codigo} titulo={inicial ? "Editar vacante" : "Nueva vacante"} />
      <form onSubmit={guardar} className="flex max-w-[900px] flex-col gap-6" noValidate>
        {errores.length > 0 && (
          <div role="alert" className="rounded-chip border border-review bg-[#FBE7D6] px-4 py-3 text-sm font-semibold text-[#7F3409]">
            <ul className="list-disc pl-5">{errores.map((e) => <li key={e}>{e}</li>)}</ul>
          </div>
        )}

        <Panel titulo="Datos del cargo">
          <div className="grid gap-5 p-5 sm:grid-cols-2">
            {campo("cargo", "Cargo")}
            {campo("cliente", "Empresa cliente (no se muestra en la web)")}
            {campo("ciudad", "Ciudad")}
            <label htmlFor={`${uid}-modalidad`} className="flex flex-col gap-1.5 text-sm font-semibold">
              Modalidad
              <select id={`${uid}-modalidad`} className={`${input} font-normal`} value={datos.modalidad} onChange={(e) => set("modalidad", e.target.value as Modalidad)}>
                <option value="presencial">Presencial</option>
                <option value="hibrido">Híbrido</option>
                <option value="remoto">Remoto</option>
              </select>
            </label>
            {campo("modalidad_detalle", "Detalle de modalidad (ej. 80 % remoto)")}
            {campo("jornada", "Jornada")}
            {campo("salario_texto", "Salario (vacío = a convenir)")}
            <div className="flex flex-col gap-3 pt-6">
              <label className="flex items-center gap-2.5 text-[15px]">
                <input type="checkbox" className="size-5 accent-action" checked={datos.urgente} onChange={(e) => set("urgente", e.target.checked)} />
                Selección urgente
              </label>
              <label className="flex items-center gap-2.5 text-[15px]">
                <input type="checkbox" className="size-5 accent-action" checked={datos.activa} onChange={(e) => set("activa", e.target.checked)} />
                Publicar en la web al guardar
              </label>
            </div>
            <label htmlFor={`${uid}-desc`} className="flex flex-col gap-1.5 text-sm font-semibold sm:col-span-2">
              Descripción del cargo
              <textarea id={`${uid}-desc`} rows={4} className="rounded-chip border border-line-strong p-3 text-base font-normal" value={datos.descripcion ?? ""} onChange={(e) => set("descripcion", e.target.value)} />
            </label>
            <label htmlFor={`${uid}-resp`} className="flex flex-col gap-1.5 text-sm font-semibold sm:col-span-2">
              Responsabilidades (una por línea)
              <textarea id={`${uid}-resp`} rows={4} className="rounded-chip border border-line-strong p-3 text-base font-normal" value={responsabilidades} onChange={(e) => setResponsabilidades(e.target.value)} />
            </label>
          </div>
        </Panel>

        <Panel titulo="Criterios de calificación (matriz Likert)">
          <p className="px-5 pt-4 text-sm text-ink-soft">
            La IA compara cada hoja de vida con estos criterios. No incluya edad, sexo, estado civil, religión, etnia ni discapacidad.
          </p>
          <Estado cargando={habilidades.estado === "cargando"} error={habilidades.error} />
          <ul className="grid gap-x-6 p-5 sm:grid-cols-2">
            {habilidades.datos?.map((h) => {
              const c = criterio(h.id);
              return (
                <li key={h.id} className="flex flex-wrap items-center gap-3 border-b border-[#ECEEF4] py-2.5">
                  <label className="flex flex-1 items-center gap-2.5 text-[15px]">
                    <input type="checkbox" className="size-5 accent-action" checked={Boolean(c)} onChange={() => alternarCriterio(h.id, h.nombre)} />
                    {h.nombre}
                  </label>
                  {c && (
                    <>
                      <label className="flex items-center gap-1.5 text-sm">
                        <input type="checkbox" className="size-4 accent-action" checked={c.obligatoria} onChange={(e) => editarCriterio(h.id, { obligatoria: e.target.checked })} />
                        Requerido
                      </label>
                      <label className="flex items-center gap-1.5 text-sm">
                        Peso
                        <select className="min-h-9 rounded-chip border border-line-strong px-1.5" value={c.peso} onChange={(e) => editarCriterio(h.id, { peso: Number(e.target.value) })}>
                          {[1, 2, 3, 4, 5].map((p) => <option key={p} value={p}>{p}</option>)}
                        </select>
                      </label>
                    </>
                  )}
                </li>
              );
            })}
          </ul>
        </Panel>

        <div className="flex gap-3">
          <button type="submit" disabled={guardando} className="min-h-11 rounded-chip bg-action px-5 font-bold text-white disabled:opacity-60">
            {guardando ? "Guardando vacante…" : inicial ? "Guardar cambios" : "Crear vacante"}
          </button>
          <button type="button" onClick={() => router.back()} className="min-h-11 rounded-chip border border-line-strong px-5 font-semibold">
            Cancelar
          </button>
        </div>
      </form>
    </>
  );
}
