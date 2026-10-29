import { AlertTriangle, CheckCircle2, Inbox, Loader2, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { ErrorApi } from "@/lib/api";
import { cn } from "@/lib/utils";

/** Estado de carga. Siempre con texto: el spinner solo no informa. */
export function Cargando({ que = "los datos" }: { que?: string }) {
  return (
    <p role="status" className="flex items-center gap-2 text-body-sm text-mh-secondary">
      <Loader2 aria-hidden="true" className="size-4 animate-spin" />
      Cargando {que}…
    </p>
  );
}

/** Estado de error de una consulta, con el `codigo` de la API cuando existe. */
export function ErrorConsulta({
  error,
  onReintentar,
}: {
  error: unknown;
  onReintentar?: () => void;
}) {
  const detalle =
    error instanceof ErrorApi ? `${error.codigo}: ${error.message}` : "Revisá que la API esté corriendo.";

  return (
    <div
      role="alert"
      className="flex flex-wrap items-center gap-3 rounded-sm border border-mh-border bg-mh-surface px-4 py-3 text-body-sm text-mh-danger"
    >
      <AlertTriangle aria-hidden="true" className="size-5 shrink-0" />
      <span className="flex-1">No se pudo cargar: {detalle}</span>
      {onReintentar ? (
        <button
          type="button"
          onClick={onReintentar}
          className="min-h-[44px] rounded-sm border border-mh-border-control px-4 text-label text-mh-text hover:bg-mh-raised"
        >
          Reintentar
        </button>
      ) : null}
    </div>
  );
}

/** Sin datos todavía: explica qué falta, no solo que está vacío. */
export function Vacio({ titulo, children }: { titulo: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-start gap-2 rounded-sm border border-dashed border-mh-border px-5 py-8">
      <p className="flex items-center gap-2 text-label text-mh-secondary">
        <Inbox aria-hidden="true" className="size-5" />
        {titulo}
      </p>
      {children ? <div className="text-body-sm text-mh-muted">{children}</div> : null}
    </div>
  );
}

type Tono = "ok" | "advertencia" | "error" | "info";

/** Tinte de superficie + color de icono por tono. El texto queda legible en los tres. */
const TONO: Record<Tono, { fondo: string; icono: string; Icono: LucideIcon }> = {
  ok: { fondo: "bg-mh-success-surface", icono: "text-mh-success", Icono: CheckCircle2 },
  advertencia: { fondo: "bg-mh-warning-surface", icono: "text-mh-warning", Icono: AlertTriangle },
  error: { fondo: "bg-mh-danger-surface", icono: "text-mh-danger", Icono: AlertTriangle },
  info: { fondo: "bg-mh-surface", icono: "text-mh-secondary", Icono: CheckCircle2 },
};

/** Aviso con icono + texto. Nunca se distingue solo por color (accesibilidad AA). */
export function Aviso({
  tono = "info",
  children,
  className,
}: {
  tono?: Tono;
  children: ReactNode;
  className?: string;
}) {
  const { fondo, icono, Icono } = TONO[tono];
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-sm border border-mh-border px-4 py-3 text-body-sm",
        fondo,
        className,
      )}
    >
      <Icono aria-hidden="true" className={cn("mt-0.5 size-5 shrink-0", icono)} />
      <div className="flex-1 text-mh-secondary">{children}</div>
    </div>
  );
}
