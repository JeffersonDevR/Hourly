import { describe, expect, it } from "vitest";

import { versionMasReciente } from "@/lib/version";

describe("versionMasReciente", () => {
  it("elige la de número más alto sin importar el orden", () => {
    const versiones = [
      { numero: 3, id: "c" },
      { numero: 1, id: "a" },
      { numero: 2, id: "b" },
    ];

    expect(versionMasReciente(versiones)?.id).toBe("c");
  });

  it("devuelve undefined sin versiones", () => {
    expect(versionMasReciente([])).toBeUndefined();
  });

  it("no muta la lista recibida", () => {
    const versiones = [{ numero: 1 }, { numero: 2 }];

    versionMasReciente(versiones);

    expect(versiones[0]?.numero).toBe(1);
  });
});
