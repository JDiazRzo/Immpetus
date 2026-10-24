"use client";

import { useMemo, useState } from "react";
import type { VacanteResumen } from "@/types/api";
import { VacancyRow } from "./VacancyRow";

const normalizar = (s: string) =>
  s.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

export function VacancyList({ vacantes }: { vacantes: VacanteResumen[] }) {
  const [busqueda, setBusqueda] = useState("");

  const filtradas = useMemo(() => {
    const q = normalizar(busqueda.trim());
    if (!q) return vacantes;
    return vacantes.filter((v) => normalizar(`${v.cargo} ${v.ciudad} ${v.modalidad_detalle ?? ""}`).includes(q));
  }, [busqueda, vacantes]);

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-6 border-b-2 border-ink pb-5">
        <div className="flex flex-col gap-2">
          <h2 className="font-display text-4xl font-extrabold tracking-tight sm:text-[44px]">Vacantes activas</h2>
          <p className="text-ink-soft">Postúlese directamente aquí. Una persona del equipo revisa cada hoja de vida.</p>
        </div>
        <label className="flex flex-col gap-1 text-sm font-semibold text-ink-soft">
          Buscar vacante
          <input
            type="search"
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Cargo, ciudad o modalidad"
            className="min-h-11 w-72 max-w-full rounded-chip border border-line-strong bg-surface px-3.5 text-base font-normal text-ink"
          />
        </label>
      </div>

      <p className="sr-only" aria-live="polite">
        {filtradas.length} vacantes encontradas
      </p>

      {filtradas.length > 0 ? (
        <ul>
          {filtradas.map((v) => (
            <VacancyRow key={v.id} vacante={v} />
          ))}
        </ul>
      ) : (
        <p className="py-10 text-ink-soft">
          No hay vacantes que coincidan con “{busqueda}”. Pruebe con otra palabra o deje su hoja de vida para futuras
          vacantes.
        </p>
      )}
    </>
  );
}
