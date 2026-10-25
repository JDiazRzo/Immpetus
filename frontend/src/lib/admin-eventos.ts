// Avisa a las pantallas del centro de mando que algo cambió para que recarguen sus datos.
const oyentes = new Set<() => void>();

export function suscribir(fn: () => void) {
  oyentes.add(fn);
  return () => {
    oyentes.delete(fn);
  };
}

export const notificar = () => oyentes.forEach((fn) => fn());
