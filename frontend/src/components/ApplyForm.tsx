"use client";

import Link from "next/link";
import { useId, useRef, useState } from "react";
import { ApiRequestError, enviarPostulacion } from "@/lib/api";
import { cn } from "@/lib/cn";
import { SITE } from "@/lib/site";

type Errores = Partial<Record<"nombre" | "correo" | "celular" | "archivo" | "autorizacion_datos", string>>;
type Estado = { tipo: "inicial" } | { tipo: "enviando" } | { tipo: "enviada" } | { tipo: "error"; mensaje: string };

const MAX_BYTES = SITE.maxPdfMb * 1024 * 1024;
const CORREO_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validar(form: FormData): Errores {
  const errores: Errores = {};
  const nombre = String(form.get("nombre") ?? "").trim();
  const correo = String(form.get("correo") ?? "").trim();
  const celular = String(form.get("celular") ?? "").replace(/\D/g, "");
  const archivo = form.get("archivo");

  if (nombre.length < 3) errores.nombre = "Escriba su nombre completo.";
  if (!CORREO_RE.test(correo)) errores.correo = "Escriba un correo válido, por ejemplo nombre@correo.com.";
  if (celular.length < 7) errores.celular = "Escriba un número de celular válido.";
  if (!(archivo instanceof File) || archivo.size === 0) {
    errores.archivo = "Adjunte su hoja de vida en PDF.";
  } else if (archivo.type !== "application/pdf") {
    errores.archivo = "El archivo debe ser PDF.";
  } else if (archivo.size > MAX_BYTES) {
    errores.archivo = `El archivo debe ser PDF de máximo ${SITE.maxPdfMb} MB.`;
  }
  if (form.get("autorizacion_datos") !== "on") {
    errores.autorizacion_datos = "Para postularse debe autorizar el tratamiento de sus datos.";
  }
  return errores;
}

export function ApplyForm({ vacanteId }: { vacanteId: string }) {
  const id = useId();
  const formRef = useRef<HTMLFormElement>(null);
  const [errores, setErrores] = useState<Errores>({});
  const [estado, setEstado] = useState<Estado>({ tipo: "inicial" });
  const [archivoNombre, setArchivoNombre] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const nuevosErrores = validar(form);
    setErrores(nuevosErrores);

    const primero = Object.keys(nuevosErrores)[0];
    if (primero) {
      formRef.current?.querySelector<HTMLElement>(`[name="${primero}"]`)?.focus();
      return;
    }

    form.set("vacante_id", vacanteId);
    form.set("autorizacion_datos", "true");
    form.set("autorizacion_futuras", form.get("autorizacion_futuras") === "on" ? "true" : "false");
    form.set("autorizacion_version", SITE.autorizacionVersion);

    setEstado({ tipo: "enviando" });
    try {
      await enviarPostulacion(form);
      setEstado({ tipo: "enviada" });
    } catch (err) {
      const mensaje =
        err instanceof ApiRequestError ? err.message : "No pudimos enviar su postulación. Intente de nuevo.";
      setEstado({ tipo: "error", mensaje });
    }
  }

  if (estado.tipo === "enviada") {
    return (
      <div role="status" className="flex flex-col gap-3">
        <h2 className="font-display text-[28px] font-extrabold tracking-tight">Postulación enviada</h2>
        <p className="leading-relaxed text-ink-soft">
          Recibimos su hoja de vida. Una persona del equipo la revisará y le escribiremos al correo que registró.
        </p>
        <Link href="/#vacantes" className="font-bold text-action">
          Ver otras vacantes
        </Link>
      </div>
    );
  }

  const campo = (name: keyof Errores) => ({
    name,
    id: `${id}-${name}`,
    "aria-invalid": errores[name] ? true : undefined,
    "aria-describedby": errores[name] ? `${id}-${name}-error` : undefined,
  });

  const mensajeError = (name: keyof Errores) =>
    errores[name] ? (
      <p id={`${id}-${name}-error`} className="text-sm font-semibold text-review">
        {errores[name]}
      </p>
    ) : null;

  const inputClase = (name: keyof Errores) =>
    cn(
      "min-h-11 w-full rounded-chip border bg-surface px-3.5 text-base text-ink",
      errores[name] ? "border-review" : "border-line-strong",
    );

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate className="flex flex-col gap-5" aria-labelledby={`${id}-titulo`}>
      <h2 id={`${id}-titulo`} className="font-display text-[28px] font-extrabold tracking-tight">
        Postularme
      </h2>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-nombre`} className="text-sm font-semibold">Nombre completo</label>
        <input type="text" autoComplete="name" className={inputClase("nombre")} {...campo("nombre")} />
        {mensajeError("nombre")}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-correo`} className="text-sm font-semibold">Correo electrónico</label>
        <input type="email" autoComplete="email" className={inputClase("correo")} {...campo("correo")} />
        {mensajeError("correo")}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-celular`} className="text-sm font-semibold">Celular</label>
        <input type="tel" autoComplete="tel" inputMode="tel" className={inputClase("celular")} {...campo("celular")} />
        {mensajeError("celular")}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-archivo`} className="text-sm font-semibold">Hoja de vida</label>
        <div
          className={cn(
            "flex flex-col gap-1 rounded-panel border-[1.5px] border-dashed bg-paper p-5",
            errores.archivo ? "border-review" : "border-[#8E93B5]",
          )}
        >
          <span className="font-semibold">{archivoNombre ?? "Seleccione su archivo PDF"}</span>
          <span className="text-[13px] text-ink-soft">Solo PDF, máximo {SITE.maxPdfMb} MB</span>
          <input
            type="file"
            accept="application/pdf"
            className="mt-2 text-sm file:mr-3 file:min-h-10 file:rounded-chip file:border-0 file:bg-ink file:px-4 file:font-semibold file:text-white"
            onChange={(e) => setArchivoNombre(e.target.files?.[0]?.name ?? null)}
            {...campo("archivo")}
          />
        </div>
        {mensajeError("archivo")}
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            className="mt-0.5 size-5 shrink-0 accent-action"
            {...campo("autorizacion_datos")}
          />
          <label htmlFor={`${id}-autorizacion_datos`} className="text-sm leading-relaxed text-[#343861]">
            Autorizo a Immpetus Soluciones a tratar mis datos personales para este proceso de selección.
            Entiendo que mi hoja de vida se analiza con apoyo de inteligencia artificial y que una persona revisa el
            resultado. Leí la{" "}
            <Link href="/politica-de-datos" className="font-semibold text-action underline underline-offset-2">
              política de tratamiento de datos
            </Link>{" "}
            (Ley 1581 de 2012).
          </label>
        </div>
        {mensajeError("autorizacion_datos")}
      </div>

      <div className="flex items-start gap-3">
        <input
          id={`${id}-autorizacion_futuras`}
          name="autorizacion_futuras"
          type="checkbox"
          className="mt-0.5 size-5 shrink-0 accent-action"
        />
        <label htmlFor={`${id}-autorizacion_futuras`} className="text-sm leading-relaxed text-[#343861]">
          <span className="font-semibold">Opcional:</span> guarden mi hoja de vida para considerarme en futuras
          vacantes que se ajusten a mi perfil.
        </label>
      </div>

      {estado.tipo === "error" && (
        <p role="alert" className="rounded-chip border border-review bg-[#FBE7D6] px-4 py-3 text-sm font-semibold text-[#7F3409]">
          {estado.mensaje}
        </p>
      )}

      <button
        type="submit"
        disabled={estado.tipo === "enviando"}
        className="min-h-12 rounded-chip bg-action px-5 text-[17px] font-bold text-white transition-colors hover:bg-ink disabled:cursor-wait disabled:opacity-70"
      >
        {estado.tipo === "enviando" ? "Enviando postulación…" : "Enviar postulación"}
      </button>
      <p className="text-[13px] text-ink-soft">Le confirmaremos por correo que recibimos su hoja de vida.</p>
    </form>
  );
}
