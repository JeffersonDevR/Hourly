import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Loader2, Sparkles } from "lucide-react";
import type { ReactNode } from "react";

import { clavesConsulta, obtenerEstado } from "@/lib/api";
import { cn } from "@/lib/utils";

type ChipProps = {
  children: ReactNode;
  tono?: "neutral" | "ok" | "error" | "muted";
};

function Chip({ children, tono = "neutral" }: ChipProps) {
  return (
    <span
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
 * Barra superior global. En la fase 0 son placeholders visibles: año e institución,
 * guardado, contador de conflictos y selector de escenario llegan con la fase 6.
 * Lo único real es el semáforo, alimentado por `GET /api/estado`.
 */
export function TopBar() {
  const estado = useQuery({
    queryKey: clavesConsulta.estado,
    queryFn: obtenerEstado,
  });

  return (
    <header className="flex h-[72px] shrink-0 items-center justify-between gap-4 border-b border-mh-border bg-mh-chrome px-6">
      <div className="flex min-w-0 items-center gap-3">
        <span className="truncate text-body-sm text-mh-secondary">2026 · Institución sin configurar</span>
      </div>

      <div className="flex items-center gap-2">
        <Chip tono="muted">
          <span aria-hidden="true">—</span>
          Conflictos
        </Chip>

        <Chip tono="muted">
          <span aria-hidden="true">—</span>
          Guardado
        </Chip>

        <Chip>
          Escenario: Base
        </Chip>

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
          <Chip tono="ok">
            <CheckCircle2 aria-hidden="true" className="size-4" />
            API conectada
          </Chip>
        ) : null}

        {estado.data ? (
          <Chip tono={estado.data.ai_disponible ? "ok" : "muted"}>
            <Sparkles aria-hidden="true" className="size-4" />
            {estado.data.ai_disponible
              ? "Asistente IA disponible"
              : "Asistente IA no disponible"}
          </Chip>
        ) : null}
      </div>
    </header>
  );
}
