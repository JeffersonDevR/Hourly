import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Sparkles, Wrench, XCircle } from "lucide-react";
import { useState } from "react";

import { Aviso, Cargando, ErrorConsulta, Vacio } from "@/components/estados";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  aceptarPropuesta,
  clavesConsulta,
  listarConflictos,
  listarVersiones,
  proponerSolucion,
  rechazarPropuesta,
  type Propuesta,
} from "@/lib/api";
import { versionMasReciente } from "@/lib/version";
import type { Conflicto } from "@/types/api";

const TIPO_CAMBIO: Record<string, string> = {
  mover_sesion: "Mover la sesión",
  cambiar_docente: "Cambiar el docente",
  cambiar_recurso: "Cambiar el aula",
};

function Chip({ tono }: { tono: "ia" | "solver" }) {
  return (
    <span
      className={
        tono === "ia"
          ? "inline-flex items-center gap-1.5 rounded-full border border-mh-ai-border px-2.5 py-1 text-label-xs text-mh-ai"
          : "inline-flex items-center gap-1.5 rounded-full border border-mh-border px-2.5 py-1 text-label-xs text-mh-secondary"
      }
    >
      {tono === "ia" ? <Sparkles aria-hidden="true" className="size-3.5" /> : <Wrench aria-hidden="true" className="size-3.5" />}
      {tono === "ia" ? "Asistente" : "Solver"}
    </span>
  );
}

function TarjetaPropuesta({
  propuesta,
  onAceptar,
  onRechazar,
  ocupada,
}: {
  propuesta: Propuesta;
  onAceptar: () => void;
  onRechazar: () => void;
  ocupada: boolean;
}) {
  return (
    <li className="rounded-cell border border-mh-border px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-label text-mh-text">{propuesta.titulo}</p>
        <Chip tono={propuesta.origen} />
      </div>
      <p className="mt-1 text-body-sm text-mh-secondary">{propuesta.explicacion}</p>
      {propuesta.impacto ? (
        <p className="mt-1 text-label-xs text-mh-muted">Impacto: {propuesta.impacto}</p>
      ) : null}
      <ul className="mt-2 flex flex-col gap-1">
        {propuesta.cambios.map((cambio) => (
          <li key={cambio.id} className="text-label-xs text-mh-secondary">
            · {TIPO_CAMBIO[cambio.tipo] ?? cambio.tipo}
            {typeof cambio.datos.dia === "number" ? ` al día ${cambio.datos.dia}` : ""}
          </li>
        ))}
      </ul>
      <div className="mt-3 flex gap-2">
        <Button size="sm" onClick={onAceptar} disabled={ocupada}>
          <CheckCircle2 aria-hidden="true" />
          Aceptar
        </Button>
        <Button size="sm" variant="outline" onClick={onRechazar} disabled={ocupada}>
          <XCircle aria-hidden="true" />
          Rechazar
        </Button>
      </div>
    </li>
  );
}

export function Conflictos() {
  const cliente = useQueryClient();
  const [elegido, setElegido] = useState<string | null>(null);
  const [propuestas, setPropuestas] = useState<Propuesta[]>([]);
  const [alerta, setAlerta] = useState<{ codigo: string; mensaje: string }[]>([]);
  const [aviso, setAviso] = useState<string | null>(null);

  const versiones = useQuery({ queryKey: clavesConsulta.versiones, queryFn: listarVersiones });
  const version = versiones.data ? versionMasReciente(versiones.data) : undefined;
  const conflictos = useQuery({
    queryKey: clavesConsulta.conflictos(version?.id ?? "sin-version"),
    queryFn: () => listarConflictos(version!.id),
    enabled: Boolean(version),
  });

  const lista = conflictos.data?.conflictos ?? [];
  const errores = lista.filter((conflicto) => conflicto.gravedad === "error");
  const detalle: Conflicto | undefined = lista.find((conflicto) => conflicto.id === elegido);

  const proponer = useMutation({
    mutationFn: (conflictoId: string) => proponerSolucion(conflictoId),
    onSuccess: (datos) => {
      setPropuestas(datos.propuestas);
      setAlerta(datos.alerta);
      setAviso(
        datos.propuestas.length === 0
          ? "Ninguna propuesta resolvió el conflicto sin crear otro."
          : null,
      );
    },
    onError: () => setAviso("No se pudo pedir una propuesta."),
  });

  const cerrar = useMutation({
    mutationFn: ({ id, aceptar }: { id: string; aceptar: boolean }) =>
      aceptar ? aceptarPropuesta(id) : rechazarPropuesta(id),
    onSuccess: async (_datos, variables) => {
      setAviso(variables.aceptar ? "Propuesta aplicada." : "Propuesta rechazada.");
      setPropuestas([]);
      setAlerta([]);
      if (version) {
        void cliente.invalidateQueries({ queryKey: clavesConsulta.conflictos(version.id) });
        void cliente.invalidateQueries({ queryKey: clavesConsulta.sesiones(version.id) });
      }
    },
    onError: () => setAviso("No se pudo cerrar la propuesta."),
  });

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Conflictos
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          {errores.length > 0
            ? `${errores.length} conflictos impiden publicar.`
            : "Sin errores: el horario se puede publicar."}
        </p>
      </div>

      {versiones.isLoading || conflictos.isLoading ? <Cargando que="los conflictos" /> : null}
      {conflictos.isError ? (
        <ErrorConsulta error={conflictos.error} onReintentar={() => void conflictos.refetch()} />
      ) : null}

      {aviso ? (
        <div aria-live="polite">
          <Aviso tono="info">{aviso}</Aviso>
        </div>
      ) : null}

      {!version && versiones.data ? (
        <Vacio titulo="Todavía no hay una versión de horario">
          Generá el horario desde <strong>Horario</strong> para que haya algo que auditar.
        </Vacio>
      ) : null}

      {version ? (
        <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
          <Card>
            <CardHeader>
              <CardTitle>Encontrados</CardTitle>
              <CardDescription>
                {lista.length} en la versión {version.numero}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {lista.length === 0 ? (
                <Vacio titulo="Sin conflictos">
                  La versión está limpia. Podés publicarla desde <strong>Publicar</strong>.
                </Vacio>
              ) : (
                <ul className="flex flex-col gap-2">
                  {lista.map((conflicto) => (
                    <li key={conflicto.id}>
                      <button
                        type="button"
                        onClick={() => {
                          setElegido(conflicto.id);
                          setPropuestas([]);
                          setAlerta([]);
                          setAviso(null);
                        }}
                        aria-pressed={conflicto.id === elegido}
                        className={
                          conflicto.id === elegido
                            ? "w-full rounded-cell border border-mh-text bg-mh-raised px-4 py-3 text-left"
                            : "w-full rounded-cell border border-mh-border px-4 py-3 text-left hover:bg-mh-raised"
                        }
                      >
                        <span className="flex flex-wrap items-center gap-2 text-label text-mh-text">
                          {conflicto.gravedad === "error" ? (
                            <AlertTriangle aria-hidden="true" className="size-4 text-mh-danger" />
                          ) : (
                            <AlertTriangle aria-hidden="true" className="size-4 text-mh-warning" />
                          )}
                          {conflicto.gravedad === "error" ? "Error" : "Advertencia"}
                          <code className="rounded-sm bg-mh-raised px-1.5 py-0.5 text-label-xs text-mh-muted">
                            {conflicto.codigo}
                          </code>
                        </span>
                        <span className="mt-1 block text-body-sm text-mh-secondary">
                          {conflicto.mensaje}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Resolución</CardTitle>
              <CardDescription>
                {detalle ? detalle.codigo : "Elegí un conflicto para ver propuestas."}
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {!detalle ? (
                <Vacio titulo="Nada seleccionado" />
              ) : (
                <>
                  <p className="text-body-sm text-mh-secondary">{detalle.mensaje}</p>
                  <p className="text-label-xs text-mh-muted">
                    {detalle.sesion_ids.length} sesión(es) afectada(s)
                  </p>
                  <Button
                    onClick={() => proponer.mutate(detalle.id)}
                    disabled={proponer.isPending}
                  >
                    <Wrench aria-hidden="true" />
                    {proponer.isPending ? "Buscando…" : "Proponer solución"}
                  </Button>
                  <span aria-live="polite" className="text-label-xs text-mh-muted">
                    {proponer.isPending ? "Probando reparación local y asistente…" : ""}
                  </span>

                  {propuestas.length > 0 ? (
                    <ul className="flex flex-col gap-3">
                      {propuestas.map((propuesta) => (
                        <TarjetaPropuesta
                          key={propuesta.id}
                          propuesta={propuesta}
                          ocupada={cerrar.isPending}
                          onAceptar={() => cerrar.mutate({ id: propuesta.id, aceptar: true })}
                          onRechazar={() => cerrar.mutate({ id: propuesta.id, aceptar: false })}
                        />
                      ))}
                    </ul>
                  ) : null}

                  {alerta.length > 0 ? (
                    <Aviso tono="advertencia">
                      <span className="block font-semibold">Qué falta para resolverlo</span>
                      <ul className="mt-1 flex flex-col gap-1">
                        {alerta.map((item) => (
                          <li key={item.codigo + item.mensaje}>· {item.mensaje}</li>
                        ))}
                      </ul>
                    </Aviso>
                  ) : null}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      ) : null}
    </section>
  );
}
