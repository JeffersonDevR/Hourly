import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

import { Aviso, Cargando, ErrorConsulta, Vacio } from "@/components/estados";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { clavesConsulta, listarDocentes, listarVersiones, vistaHorario } from "@/lib/api";
import { versionMasReciente } from "@/lib/version";

/** Barra de carga semanal: sesiones colocadas contra el máximo del docente. */
function BarraCarga({ sesiones, maximo }: { sesiones: number; maximo: number }) {
  const exceso = sesiones > maximo;
  const porcentaje = maximo > 0 ? Math.min(100, Math.round((sesiones / maximo) * 100)) : 100;
  const etiqueta = `${sesiones} de ${maximo} sesiones semanales${exceso ? ", excedido" : ""}`;

  return (
    <div className="flex flex-col gap-1">
      <div
        role="progressbar"
        aria-valuenow={sesiones}
        aria-valuemin={0}
        aria-valuemax={maximo}
        aria-label={etiqueta}
        className="h-2 w-full overflow-hidden rounded-full bg-mh-sunken"
      >
        <div
          className={exceso ? "h-full bg-mh-danger" : "h-full bg-mh-accent"}
          style={{ width: `${porcentaje}%` }}
        />
      </div>
      <p className="flex items-center gap-1.5 text-label-xs text-mh-secondary">
        {exceso ? (
          <AlertTriangle aria-hidden="true" className="size-3.5 text-mh-danger" />
        ) : (
          <CheckCircle2 aria-hidden="true" className="size-3.5 text-mh-success" />
        )}
        {etiqueta}
      </p>
    </div>
  );
}

export function Docentes() {
  const docentes = useQuery({ queryKey: clavesConsulta.docentes, queryFn: listarDocentes });
  const versiones = useQuery({ queryKey: clavesConsulta.versiones, queryFn: listarVersiones });

  const version = versiones.data ? versionMasReciente(versiones.data) : undefined;
  const sesiones = useQuery({
    queryKey: clavesConsulta.sesiones(version?.id ?? "sin-version"),
    queryFn: () => vistaHorario(version!.id),
    enabled: Boolean(version),
  });

  const fallida = docentes.isError ? docentes : sesiones.isError ? sesiones : null;
  const cargando = docentes.isPending || (Boolean(version) && sesiones.isPending);

  const porDocente = new Map<string, number>();
  for (const sesion of sesiones.data?.sesiones ?? []) {
    porDocente.set(sesion.docente_id, (porDocente.get(sesion.docente_id) ?? 0) + 1);
  }
  const excedidos = (docentes.data ?? []).filter(
    (docente) => (porDocente.get(docente.id) ?? 0) > docente.max_sesiones_semana,
  );

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Docentes
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          La carga se cuenta en sesiones (bloques), no en horas. Un docente inactivo queda fuera del
          pool de asignación.
        </p>
      </div>

      {cargando ? <Cargando que="los docentes" /> : null}
      {fallida ? <ErrorConsulta error={fallida.error} onReintentar={() => void fallida.refetch()} /> : null}

      {!version && docentes.data ? (
        <Aviso tono="info">
          Todavía no hay una versión de horario: las barras muestran 0 sesiones colocadas.
        </Aviso>
      ) : null}

      {excedidos.length > 0 ? (
        <Aviso tono="error">
          {excedidos.length} docentes por encima de su máximo semanal: el solver va a devolver
          infactible hasta que se reasigne carga.
        </Aviso>
      ) : null}

      {docentes.data?.length === 0 ? (
        <Vacio titulo="Todavía no hay docentes">
          Importá el Excel de la escuela desde <strong>Importar</strong>.
        </Vacio>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(docentes.data ?? []).map((docente) => (
          <Card key={docente.id}>
            <CardHeader>
              <CardTitle>
                {docente.codigo} · {docente.nombre}
              </CardTitle>
              <CardDescription>
                {docente.activo ? "Activo" : "Inactivo · fuera del pool de asignación"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <BarraCarga
                sesiones={porDocente.get(docente.id) ?? 0}
                maximo={docente.max_sesiones_semana}
              />
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
