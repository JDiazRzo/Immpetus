"use client";

import Link from "next/link";
import { useId, useRef, useState } from "react";
import { ApiRequestError, enviarContacto } from "@/lib/api";
import { cn } from "@/lib/cn";
import { SERVICIOS_CONTACTO, type ServicioContacto } from "@/types/api";

type Campo = "nombre" | "correo" | "mensaje" | "autorizacion_datos";
type Errores = Partial<Record<Campo, string>>;
type Estado = { tipo: "inicial" } | { tipo: "enviando" } | { tipo: "enviado" } | { tipo: "error"; mensaje: string };

const CORREO_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validar(form: FormData): Errores {
  const errores: Errores = {};
  if (String(form.get("nombre") ?? "").trim().length < 3) errores.nombre = "Escriba su nombre.";
  if (!CORREO_RE.test(String(form.get("correo") ?? "").trim())) errores.correo = "Escriba un correo válido.";
  if (String(form.get("mensaje") ?? "").trim().length < 10) errores.mensaje = "Cuéntenos un poco más (mínimo 10 caracteres).";
  if (form.get("autorizacion_datos") !== "on") errores.autorizacion_datos = "Debe autorizar el tratamiento de sus datos para que lo contactemos.";
  return errores;
}

const texto = (form: FormData, campo: string) => String(form.get(campo) ?? "").trim() || null;

export function ContactForm() {
  const id = useId();
  const formRef = useRef<HTMLFormElement>(null);
  const [errores, setErrores] = useState<Errores>({});
  const [estado, setEstado] = useState<Estado>({ tipo: "inicial" });

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);

    // Campo trampa: las personas no lo ven; si viene lleno, es un bot.
    if (texto(form, "sitio_web")) {
      setEstado({ tipo: "enviado" });
      return;
    }

    const nuevos = validar(form);
    setErrores(nuevos);
    const primero = Object.keys(nuevos)[0];
    if (primero) {
      formRef.current?.querySelector<HTMLElement>(`[name="${primero}"]`)?.focus();
      return;
    }

    setEstado({ tipo: "enviando" });
    try {
      await enviarContacto({
        nombre: texto(form, "nombre") ?? "",
        empresa: texto(form, "empresa"),
        correo: texto(form, "correo") ?? "",
        telefono: texto(form, "telefono"),
        servicio: (texto(form, "servicio") as ServicioContacto | null) ?? null,
        mensaje: texto(form, "mensaje") ?? "",
        autorizacion_datos: true,
      });
      setEstado({ tipo: "enviado" });
    } catch (err) {
      setEstado({
        tipo: "error",
        mensaje: err instanceof ApiRequestError ? err.message : "No pudimos enviar su mensaje. Intente de nuevo.",
      });
    }
  }

  if (estado.tipo === "enviado") {
    return (
      <div role="status" className="flex flex-col gap-3 rounded-2xl border border-line bg-paper p-6">
        <h3 className="font-display text-2xl font-extrabold tracking-tight">Mensaje enviado</h3>
        <p className="leading-relaxed text-ink-soft">Gracias. Un consultor le responderá al correo que registró.</p>
      </div>
    );
  }

  const attrs = (name: Campo) => ({
    name,
    id: `${id}-${name}`,
    "aria-invalid": errores[name] ? true : undefined,
    "aria-describedby": errores[name] ? `${id}-${name}-error` : undefined,
  });
  const error = (name: Campo) =>
    errores[name] ? (
      <p id={`${id}-${name}-error`} className="text-sm font-semibold text-review">
        {errores[name]}
      </p>
    ) : null;
  const clase = (name?: Campo) =>
    cn(
      "min-h-11 w-full rounded-chip border bg-surface px-3.5 text-base text-ink",
      name && errores[name] ? "border-review" : "border-line-strong",
    );
  const etiqueta = "text-sm font-semibold";
  const requerido = <span aria-hidden="true" className="text-review"> *</span>;

  return (
    <form ref={formRef} onSubmit={onSubmit} noValidate className="grid gap-5 sm:grid-cols-2" aria-label="Formulario de contacto">
      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-nombre`} className={etiqueta}>Nombre{requerido}</label>
        <input {...attrs("nombre")} autoComplete="name" required className={clase("nombre")} />
        {error("nombre")}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-empresa`} className={etiqueta}>Empresa</label>
        <input id={`${id}-empresa`} name="empresa" autoComplete="organization" className={clase()} />
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-correo`} className={etiqueta}>Correo{requerido}</label>
        <input {...attrs("correo")} type="email" autoComplete="email" required className={clase("correo")} />
        {error("correo")}
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={`${id}-telefono`} className={etiqueta}>Teléfono / WhatsApp</label>
        <input id={`${id}-telefono`} name="telefono" type="tel" autoComplete="tel" className={clase()} />
      </div>

      <div className="flex flex-col gap-1.5 sm:col-span-2">
        <label htmlFor={`${id}-servicio`} className={etiqueta}>Servicio de interés</label>
        <select id={`${id}-servicio`} name="servicio" defaultValue="" className={clase()}>
          <option value="">Seleccione una opción</option>
          {SERVICIOS_CONTACTO.map((s) => (
            <option key={s.valor} value={s.valor}>{s.etiqueta}</option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1.5 sm:col-span-2">
        <label htmlFor={`${id}-mensaje`} className={etiqueta}>Mensaje{requerido}</label>
        <textarea {...attrs("mensaje")} rows={5} required maxLength={2000} className={cn(clase("mensaje"), "py-2.5")} />
        {error("mensaje")}
      </div>

      {/* Trampa para bots: oculta para personas y lectores de pantalla */}
      <div aria-hidden="true" className="absolute -left-[9999px] size-px overflow-hidden">
        <label htmlFor={`${id}-sitio_web`}>No llenar</label>
        <input id={`${id}-sitio_web`} name="sitio_web" tabIndex={-1} autoComplete="off" />
      </div>

      <div className="flex flex-col gap-1.5 sm:col-span-2">
        <div className="flex items-start gap-3">
          <input {...attrs("autorizacion_datos")} type="checkbox" className="mt-0.5 size-5 shrink-0 accent-action" />
          <label htmlFor={`${id}-autorizacion_datos`} className="text-sm leading-relaxed text-[#343861]">
            Autorizo a Immpetus Soluciones a usar estos datos solo para responder mi solicitud. Leí la{" "}
            <Link href="/politica-de-datos" className="font-semibold text-action underline underline-offset-2">
              política de tratamiento de datos
            </Link>
            .{requerido}
          </label>
        </div>
        {error("autorizacion_datos")}
      </div>

      {estado.tipo === "error" && (
        <p role="alert" className="rounded-chip border border-review bg-[#FBE7D6] px-4 py-3 text-sm font-semibold text-[#7F3409] sm:col-span-2">
          {estado.mensaje}
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3 sm:col-span-2">
        <p className="text-xs text-ink-soft"><span className="text-review">*</span> Campos obligatorios</p>
        <button
          type="submit"
          disabled={estado.tipo === "enviando"}
          className="min-h-11 rounded-chip bg-action px-6 font-bold text-white disabled:opacity-60"
        >
          {estado.tipo === "enviando" ? "Enviando…" : "Enviar mensaje"}
        </button>
      </div>
    </form>
  );
}
