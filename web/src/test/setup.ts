import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// Sin `globals: true` en vitest.config, el auto-cleanup de Testing Library no se
// registra y el DOM de un test se filtra al siguiente ("found multiple elements").
afterEach(() => {
  cleanup();
});
