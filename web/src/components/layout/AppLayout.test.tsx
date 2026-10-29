import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AppLayout } from "@/components/layout/AppLayout";

function viewport(ancho: number) {
  vi.stubGlobal("matchMedia", (texto: string) => ({
    matches: ancho < 768 ? texto.includes("767") : false,
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
  const cliente = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={cliente}>
      <MemoryRouter>
        <AppLayout />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AppLayout", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("por debajo de 768 avisa en vez de comprimir el layout", () => {
    viewport(375);
    montar();

    expect(screen.getByRole("heading", { name: /necesita una pantalla más grande/i })).toBeInTheDocument();
    // No se monta la navegación: no hay layout, hay un aviso.
    expect(screen.queryByRole("navigation", { name: /navegación principal/i })).not.toBeInTheDocument();
  });

  it("en escritorio monta la navegación completa", () => {
    viewport(1440);
    montar();

    expect(screen.getByRole("navigation", { name: /navegación principal/i })).toBeInTheDocument();
  });
});
