import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Reglas } from "@/pages/Reglas";

const DOCENTES = [{ id: "d1", codigo: "D1", nombre: "Ana Torres", max_sesiones_semana: 24, activo: true }];
const BLOQUES = [
  { id: "b1", codigo: "B1", orden: 1, inicio: "07:00:00", fin: "08:00:00", duracion_min: 60, tipo: "clase" },
];

function montar() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <Reglas />
    </QueryClientProvider>,
  );
}

describe("Reglas", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        const ruta = String(url);
        if (ruta.includes("/api/reglas/interpretar")) {
          expect(JSON.parse(String(init?.body)).texto).toBe("D1 no puede los martes");
          return {
            ok: true,
            status: 200,
            json: async () => ({
              regla: {
                docente_codigo: "D1",
                docente_nombre: "Ana Torres",
                dias: [2],
                bloque_codigo: null,
                bloquea: true,
                motivo: null,
              },
              origen: "determinista",
              mensaje: null,
            }),
          };
        }
        if (ruta.includes("/api/reglas/confirmar")) {
          return { ok: true, status: 200, json: async () => ({ creados: 6, eliminados: 0, bloques: [] }) };
        }
        if (ruta.includes("/api/docentes")) return { ok: true, status: 200, json: async () => DOCENTES };
        if (ruta.includes("/api/bloques")) return { ok: true, status: 200, json: async () => BLOQUES };
        return { ok: true, status: 200, json: async () => ({}) };
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("interpreta la frase y muestra la tarjeta editable", async () => {
    const usuario = userEvent.setup();
    montar();

    await usuario.type(await screen.findByLabelText(/regla en lenguaje natural/i), "D1 no puede los martes");
    await usuario.click(screen.getByRole("button", { name: /interpretar/i }));

    expect(await screen.findByText("Regla interpretada")).toBeInTheDocument();
    expect(screen.getByText(/Interpretada por reglas/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Martes" })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Lunes" })).toHaveAttribute("aria-pressed", "false");
  });

  it("confirma la regla y reporta las franjas escritas", async () => {
    const usuario = userEvent.setup();
    montar();

    await usuario.type(await screen.findByLabelText(/regla en lenguaje natural/i), "D1 no puede los martes");
    await usuario.click(screen.getByRole("button", { name: /interpretar/i }));
    await usuario.click(await screen.findByRole("button", { name: /confirmar regla/i }));

    expect(await screen.findByText(/6 franja\(s\) bloqueada\(s\)/)).toBeInTheDocument();
  });
});
