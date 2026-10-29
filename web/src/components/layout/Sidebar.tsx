import { NavLink, Link } from "react-router-dom";

import { Marca } from "@/components/layout/Marca";
import { NAVEGACION, NAVEGACION_SECUNDARIA } from "@/lib/navegacion";
import { cn } from "@/lib/utils";

const claseItem =
  "flex min-h-[56px] flex-col items-center justify-center gap-1 rounded-cell px-1 py-1.5 text-center text-label-xs leading-tight transition-colors hover:bg-mh-raised active:bg-mh-sunken [hyphens:auto]";

/**
 * Barra lateral de `--mh-rail-width` (88px, 72px por debajo de 1280). Lockup vertical
 * de la marca: el horizontal no cabe. Las etiquetas nunca se ocultan (regla de diseño).
 */
export function Sidebar() {
  return (
    <aside className="flex h-full w-[var(--mh-rail-width)] shrink-0 flex-col overflow-hidden border-r border-mh-border bg-mh-chrome">
      <Link
        to="/"
        className="flex flex-col items-center gap-1.5 border-b border-mh-border py-4"
        aria-label="Hourly, ir a Inicio"
      >
        <span className="text-mh-text">
          <Marca alto={32} etiqueta={false} />
        </span>
        <span className="text-[15px] font-semibold leading-5 tracking-[-0.02em] text-mh-text">
          Hourly
        </span>
      </Link>

      <nav aria-label="Navegación principal" className="mh-scroll-y min-h-0 flex-1 px-1.5 py-3">
        <ul className="flex flex-col gap-1">
          {NAVEGACION.map(({ ruta, etiqueta, icono: Icono }) => (
            <li key={ruta}>
              <NavLink
                to={ruta}
                end={ruta === "/"}
                className={({ isActive }) =>
                  cn(
                    claseItem,
                    "text-mh-secondary",
                    isActive && "bg-mh-raised text-mh-text",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Icono aria-hidden="true" className="size-5 shrink-0" />
                    <span className="w-full">{etiqueta}</span>
                    <span className="sr-only">{isActive ? " (pantalla actual)" : ""}</span>
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>

        <p className="mt-5 px-1 pb-1 text-center text-label-xs text-mh-muted">Configuración</p>
        <ul className="flex flex-col gap-1">
          {NAVEGACION_SECUNDARIA.map(({ ruta, etiqueta, icono: Icono }) => (
            <li key={ruta}>
              <NavLink
                to={ruta}
                className={({ isActive }) =>
                  cn(claseItem, "min-h-[44px] text-mh-muted", isActive && "bg-mh-raised text-mh-text")
                }
              >
                <Icono aria-hidden="true" className="size-4 shrink-0" />
                <span className="w-full">{etiqueta}</span>
              </NavLink>
            </li>
          ))}
        </ul>

        <div
          aria-disabled="true"
          className="mt-5 rounded-cell border border-dashed border-mh-border px-1 py-2 text-center text-label-xs text-mh-muted"
        >
          Fase 2: usuarios
        </div>
      </nav>
    </aside>
  );
}
