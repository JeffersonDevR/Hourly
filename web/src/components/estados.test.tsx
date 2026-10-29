import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Aviso, Cargando, ErrorConsulta, Vacio } from "@/components/estados";
import { ErrorApi } from "@/lib/api";

describe("estados de consulta", () => {
  it("Cargando anuncia con role=status y texto", () => {
    render(<Cargando que="los docentes" />);

    const estado = screen.getByRole("status");

    expect(estado).toHaveTextContent("Cargando los docentes");
  });

  it("ErrorConsulta muestra el código y el mensaje de la API", () => {
    render(<ErrorConsulta error={new ErrorApi(409, "CURSO_DOBLE", "Esa franja ya está ocupada.")} />);

    const alerta = screen.getByRole("alert");

    expect(alerta).toHaveTextContent("CURSO_DOBLE: Esa franja ya está ocupada.");
  });

  it("ErrorConsulta ofrece reintentar cuando hay handler", () => {
    let reintentos = 0;
    render(
      <ErrorConsulta error={new Error("sin red")} onReintentar={() => (reintentos += 1)} />,
    );

    screen.getByRole("button", { name: "Reintentar" }).click();

    expect(reintentos).toBe(1);
  });

  it("Vacio explica qué falta", () => {
    render(<Vacio titulo="Todavía no hay cursos">Importá el Excel.</Vacio>);

    expect(screen.getByText("Todavía no hay cursos")).toBeInTheDocument();
    expect(screen.getByText("Importá el Excel.")).toBeInTheDocument();
  });

  it("Aviso no depende solo del color: siempre hay texto", () => {
    render(<Aviso tono="error">3 conflictos que impiden publicar.</Aviso>);

    expect(screen.getByText("3 conflictos que impiden publicar.")).toBeInTheDocument();
  });
});
