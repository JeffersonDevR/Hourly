import { NavLink } from "react-router-dom";

import { NAVEGACION } from "@/lib/navegacion";
import { cn } from "@/lib/utils";

/** Navegación lateral fija: las 9 rutas del MVP + el aviso de Fase 2. */
export function Sidebar() {
  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-mh-border bg-mh-chrome">
      <div className="flex h-[72px] items-center gap-3 border-b border-mh-border px-5">
        <span
          aria-hidden="true"
          className="flex size-9 items-center justify-center rounded-cell bg-mh-accent text-label-xs text-mh-on-accent"
        >
          H
        </span>
        <span className="text-h3 tracking-[-0.02em] text-mh-text">Hourly</span>
      </div>

      <nav aria-label="Navegación principal" className="flex-1 overflow-y-auto px-3 py-4">
        <ul className="flex flex-col gap-1">
          {NAVEGACION.map(({ ruta, etiqueta, icono: Icono }) => (
            <li key={ruta}>
              <NavLink
                to={ruta}
                end={ruta === "/"}
                className={({ isActive }) =>
                  cn(
                    "flex min-h-[44px] items-center gap-3 rounded-cell px-4 text-label text-mh-secondary transition-colors hover:bg-mh-raised hover:text-mh-text",
                    isActive && "bg-mh-raised text-mh-text",
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Icono aria-hidden="true" className="size-5 shrink-0" />
                    <span className="flex-1">{etiqueta}</span>
                    {isActive ? (
                      <span
                        aria-hidden="true"
                        className="h-5 w-1 rounded-full bg-mh-accent"
                      />
                    ) : null}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>

        <p className="mt-6 px-4 pb-2 text-label-xs uppercase tracking-[0.08em] text-mh-muted">
          Fase 2
        </p>
        <div
          aria-disabled="true"
          className="flex min-h-[44px] cursor-not-allowed items-center gap-3 rounded-cell px-4 text-body-sm text-mh-muted"
        >
          Próximamente: Usuarios y Vistas móviles
        </div>
      </nav>

      <div className="border-t border-mh-border px-5 py-4 text-label-xs text-mh-muted">v0.1.0</div>
    </aside>
  );
}
