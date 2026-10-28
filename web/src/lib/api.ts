import type { Estado } from "@/types/estado";

/** `GET /api/estado` — pasa por el proxy de Vite en dev. */
export async function obtenerEstado(): Promise<Estado> {
  const respuesta = await fetch("/api/estado", {
    headers: { Accept: "application/json" },
  });

  if (!respuesta.ok) {
    throw new Error(`La API respondio ${respuesta.status}`);
  }

  return (await respuesta.json()) as Estado;
}

export const clavesConsulta = {
  estado: ["estado"] as const,
};
