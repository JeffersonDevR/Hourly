import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Configuracion } from "@/pages/Configuracion";

const pedidos: { url: string; metodo: string; cuerpo: unknown }[] = [];

function montar() {
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter>
        <Configuracion />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Configuración", () => {
  beforeEach(() => {
    pedidos.length = 0;
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        pedidos.push({
          url: String(url),
          metodo: init?.method ?? "GET",
          cuerpo: init?.body ? JSON.parse(String(init.body)) : null,
        });
        return { ok: true, status: 200, json: async () => [] };
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("carga un grado a mano, sin Excel", async () => {
    const usuario = userEvent.setup();
    montar();

    const form = await screen.findByRole("form", { name: "Agregar Grados" });
    await usuario.type(within(form).getByLabelText("Nombre"), "Octavo");
    await usuario.click(within(form).getByRole("button", { name: /agregar/i }));

    const alta = pedidos.find((p) => p.metodo === "POST" && p.url.includes("/api/grados"));
    expect(alta?.cuerpo).toEqual({ nombre: "Octavo", orden: 1 });
  });

  it("un bloque de recreo se carga con su tipo", async () => {
    const usuario = userEvent.setup();
    montar();

    const form = await screen.findByRole("form", { name: "Agregar Bloques" });
    await usuario.type(within(form).getByLabelText("Código"), "R2");
    await usuario.selectOptions(within(form).getByLabelText("Tipo"), "descanso");
    await usuario.click(within(form).getByRole("button", { name: /agregar/i }));

    const alta = pedidos.find((p) => p.metodo === "POST" && p.url.includes("/api/bloques"));
    expect(alta?.cuerpo).toMatchObject({ codigo: "R2", tipo: "descanso" });
  });

  it("ofrece las nueve secciones del catálogo", async () => {
    montar();

    for (const titulo of [
      "Grados",
      "Bloques",
      "Asignaturas",
      "Tipos de recurso",
      "Cursos",
      "Docentes",
      "Recursos",
      "Carga académica",
      "Aptitudes",
    ]) {
      expect(await screen.findByRole("form", { name: `Agregar ${titulo}` })).toBeInTheDocument();
    }
  });
});
