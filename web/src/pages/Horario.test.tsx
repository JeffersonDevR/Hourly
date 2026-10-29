import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { Horario } from "@/pages/Horario";

const CURSO = { id: "c1", codigo: "6A", nombre: "Sexto A", grado_id: "g1", estudiantes: 30 };
const DOCENTE = {
  id: "d1",
  codigo: "D1",
  nombre: "Marta",
  max_sesiones_semana: 24,
  activo: true,
};
const RECURSO = {
  id: "r1",
  codigo: "A6A",
  nombre: "Aula 6A",
  tipo_recurso: "GENERAL",
  capacidad: 30,
  curso_titular_id: "c1",
};
const ASIGNATURA = { id: "a1", nombre: "Matemática", color: "#2563EB", es_pesada: false };
const ASIGNACION = {
  id: "ac1",
  curso_id: "c1",
  asignatura_id: "a1",
  docente_principal_id: "d1",
  sesiones_semana: 2,
  tipo_recurso_requerido: "GENERAL",
};
const VERSION = {
  id: "v1",
  numero: 1,
  estado: "borrador",
  escenario_id: null,
  nota: null,
  publicado_at: null,
};
const BLOQUES = [
  { id: "b1", codigo: "B1", orden: 1, inicio: "07:00:00", fin: "08:00:00", duracion_min: 60, tipo: "clase" },
  { id: "b2", codigo: "B2", orden: 2, inicio: "08:00:00", fin: "09:00:00", duracion_min: 60, tipo: "clase" },
  { id: "r1", codigo: "R1", orden: 3, inicio: "09:00:00", fin: "09:20:00", duracion_min: 20, tipo: "descanso" },
];
const SESION = {
  id: "s1",
  horario_version_id: "v1",
  asignacion_carga_id: "ac1",
  curso_id: "c1",
  docente_id: "d1",
  dia: 1,
  bloque_id: "b1",
  recurso_id: "r1",
  fijada: false,
};

const RUTAS: [string, unknown][] = [
  ["/api/horarios/v1/vista", { por: "curso", sesiones: [SESION] }],
  ["/api/horarios", [VERSION]],
  ["/api/bloques", BLOQUES],
  ["/api/cursos", [CURSO]],
  ["/api/docentes", [DOCENTE]],
  ["/api/recursos", [RECURSO]],
  ["/api/asignaturas", [ASIGNATURA]],
  ["/api/asignaciones", [ASIGNACION]],
];

function respuestaPara(url: string): unknown {
  const encontrada = RUTAS.find(([ruta]) => url.includes(ruta));
  return encontrada ? encontrada[1] : {};
}

function viewport(consulta: "compacta" | "ancha") {
  vi.stubGlobal("matchMedia", (texto: string) => ({
    matches: consulta === "compacta" ? texto.includes("1023") : false,
    media: texto,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  }));
}

function montar() {
  const cliente = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter>
        <Horario />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("Horario", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => ({
        ok: true,
        status: 200,
        json: async () => respuestaPara(String(url)),
      })),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("por debajo de 1024 muestra un día a la vez, con selector", async () => {
    const usuario = userEvent.setup();
    viewport("compacta");
    montar();

    const grilla = await screen.findByRole("table", { name: /horario semanal/i });

    expect(within(grilla).getAllByRole("columnheader")).toHaveLength(2); // Bloque + 1 día
    expect(screen.getByRole("button", { name: "Lunes" })).toHaveAttribute("aria-pressed", "true");
    expect((await within(grilla).findAllByText("Matemática")).length).toBeGreaterThan(0);

    // Al cambiar de día, la sesión del lunes deja de verse.
    await usuario.click(screen.getByRole("button", { name: "Martes" }));
    expect(within(grilla).queryByText("Matemática")).not.toBeInTheDocument();
  });

  it("dibuja la grilla con los bloques de clase como filas", async () => {
    montar();

    const grilla = await screen.findByRole("table", { name: /horario semanal/i });

    expect(within(grilla).getByRole("rowheader", { name: /B1/ })).toBeInTheDocument();
    expect(within(grilla).getByRole("rowheader", { name: /B2/ })).toBeInTheDocument();
    expect(within(grilla).getAllByRole("columnheader")[0]).toHaveTextContent("Bloque");
  });

  it("muestra los recreos como filas del horario, sin sesiones", async () => {
    montar();

    const grilla = await screen.findByRole("table", { name: /horario semanal/i });

    expect(within(grilla).getByRole("rowheader", { name: /R1/ })).toBeInTheDocument();
    expect(within(grilla).getByText(/Recreo/)).toBeInTheDocument();
    expect(within(grilla).getByText(/Sin sesiones/)).toBeInTheDocument();
  });

  it("dibuja la sesión colocada con asignatura, docente y aula", async () => {
    montar();

    const grilla = await screen.findByRole("table", { name: /horario semanal/i });

    expect((await within(grilla).findAllByText("Matemática")).length).toBeGreaterThan(0);
    expect(within(grilla).getByText(/D1 · A6A/)).toBeInTheDocument();
  });

  it("muestra en 'Por colocar' lo que falta según la malla", async () => {
    montar();

    // sesiones_semana = 2, colocada = 1  =>  falta 1
    expect(await screen.findByText("faltan 1")).toBeInTheDocument();
    expect(await screen.findByText(/0 de 2 sesiones colocadas|1 de 2 sesiones colocadas/)).toBeInTheDocument();
  });

  it("ofrece la alternativa por teclado para mover", async () => {
    montar();

    expect(await screen.findByRole("combobox", { name: /Sesión/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Mover" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Quitar" })).toBeInTheDocument();
  });
});
