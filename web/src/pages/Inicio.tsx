import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { clavesConsulta, obtenerEstado } from "@/lib/api";

/** Inicio. En la fase 0 solo prueba el cableado web → API; el checklist llega en la fase 6. */
export function Inicio() {
  const estado = useQuery({
    queryKey: clavesConsulta.estado,
    queryFn: obtenerEstado,
  });

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Inicio
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          Houry arma el horario escolar sin solapamientos: importa el Excel, audita los conflictos,
          genera el horario y publícalo.
        </p>
      </div>

      <Card className="max-w-[520px]">
        <CardHeader>
          <CardTitle>Estado del sistema</CardTitle>
          <CardDescription>
            Respuesta de <code className="text-mh-text">GET /api/estado</code>.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {estado.isPending ? (
            <p className="flex items-center gap-2 text-body-sm text-mh-secondary">
              <Loader2 aria-hidden="true" className="size-4 animate-spin" />
              Consultando la API…
            </p>
          ) : null}

          {estado.isError ? (
            <p className="flex items-center gap-2 text-body-sm text-mh-danger">
              <AlertTriangle aria-hidden="true" className="size-4" />
              No se pudo consultar la API. Revisá que el backend esté corriendo en el puerto 8000.
            </p>
          ) : null}

          {estado.data ? (
            <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-body-sm">
              <dt className="text-mh-muted">API</dt>
              <dd className="flex items-center gap-2 text-mh-success">
                <CheckCircle2 aria-hidden="true" className="size-4" />
                Conectada
              </dd>
              <dt className="text-mh-muted">Asistente IA</dt>
              <dd className="flex items-center gap-2 text-mh-secondary">
                <AlertTriangle aria-hidden="true" className="size-4" />
                {estado.data.ai_disponible ? "Disponible" : "No disponible"}
              </dd>
            </dl>
          ) : null}

          <div
            role="status"
            className="mt-5 flex items-center gap-2 rounded-sm border border-mh-border px-3 py-2 text-label-xs text-mh-muted"
          >
            El checklist de configuración y el resumen llegan en la fase 6.
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
