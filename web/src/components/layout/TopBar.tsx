import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import { useLocation } from "react-router-dom";

import { Marca } from "@/components/layout/Marca";
import { NAVEGACION, NAVEGACION_SECUNDARIA } from "@/lib/navegacion";

import {
  clavesConsulta,
  listarConflictos,
  listarEscenarios,
  listarVersiones,
  obtenerEstado,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { versionMasReciente } from "@/lib/version";

function Chip({
  children,
  tono = "neutral",
  etiqueta,
}: {
  children: ReactNode;
  tono?: "neutral" | "ok" | "error" | "muted";
  etiqueta?: string;
}) {
  return (
    <span
      aria-label={etiqueta}
      className={cn(
        "inline-flex min-h-[36px] items-center gap-2 rounded-full border px-3 text-label-xs",
        tono === "neutral" && "border-mh-border text-mh-secondary",
        tono === "muted" && "border-mh-border text-mh-muted",
        tono === "ok" && "border-mh-border text-mh-success",
        tono === "error" && "border-mh-border text-mh-danger",
      )}
    >
      {children}
    </span>
  );
}

/**
 * Barra superior global. El semáforo, el contador de conflictos y el escenario salen de
 * la versión más reciente. No hay chip de "guardado": cada mutación es una request que
 * commitea o falla, y el estado de la versión ya lo dice.
 */
export function TopBar() {
  const { pathname } = useLocation();
  const actual = [...NAVEGACION, ...NAVEGACION_SECUNDARIA].find((item) => item.ruta === pathname);

  const estado = useQuery({ queryKey: clavesConsulta.estado, queryFn: obtenerEstado });
  const versiones = useQuery({ queryKey: clavesConsulta.versiones, queryFn: listarVersiones });
  const escenarios = useQuery({ queryKey: clavesConsulta.escenarios, queryFn: listarEscenarios });

  const version = versiones.data ? versionMasReciente(versiones.data) : undefined;
  const conflictos = useQuery({
    queryKey: clavesConsulta.conflictos(version?.id ?? "sin-version"),
    queryFn: () => listarConflictos(version!.id),
    enabled: Boolean(version),
  });

  const lista = conflictos.data?.conflictos ?? [];
  const errores = lista.filter((conflicto) => conflicto.gravedad === "error").length;
  const advertencias = lista.length - errores;
  const escenario = escenarios.data?.find((item) => item.id === version?.escenario_id);

  return (
    <header className="flex min-h-[72px] shrink-0 flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-mh-border bg-mh-chrome px-4 py-2 md:px-6">
      <div className="flex min-w-0 items-center gap-3">
        <span className="text-mh-text">
          <Marca alto={24} etiqueta={false} />
        </span>
        <span aria-hidden="true" className="h-6 w-px bg-mh-border" />
        <span aria-current="page" className="truncate text-body-sm text-mh-secondary">
          {actual?.etiqueta ?? "Inicio"}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Chip tono="muted">
          {version ? `Versión ${version.numero} · ${version.estado}` : "Sin versión"}
        </Chip>

        {version ? (
          <Chip
            tono={errores > 0 ? "error" : advertencias > 0 ? "neutral" : "ok"}
            etiqueta={`${errores} errores y ${advertencias} advertencias`}
          >
            {errores > 0 ? (
              <AlertTriangle aria-hidden="true" className="size-4" />
            ) : (
              <CheckCircle2 aria-hidden="true" className="size-4" />
            )}
            {errores > 0
              ? `${errores} conflictos`
              : advertencias > 0
                ? `${advertencias} avisos`
                : "Sin conflictos"}
          </Chip>
        ) : (
          <Chip tono="muted">Sin versión de horario</Chip>
        )}

        <Chip tono="muted">Escenario: {escenario?.nombre ?? "Base"}</Chip>

        {estado.isPending ? (
          <Chip>
            <Loader2 aria-hidden="true" className="size-4 animate-spin" />
            Consultando API
          </Chip>
        ) : null}

        {estado.isError ? (
          <Chip tono="error">
            <AlertTriangle aria-hidden="true" className="size-4" />
            API sin conexión
          </Chip>
        ) : null}

        {estado.data ? (
          <Chip tono={estado.data.ai_disponible ? "ok" : "muted"}>
            <Sparkles aria-hidden="true" className="size-4" />
            {estado.data.ai_disponible ? "Asistente IA disponible" : "Asistente IA no disponible"}
          </Chip>
        ) : null}
      </div>
    </header>
  );
}
