import { useMutation, useQuery } from "@tanstack/react-query";
import { AlertTriangle, CalendarClock, CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

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
  clavesConsulta,
  listarEscenarios,
  listarVersiones,
  probarEscenario,
  type ProspectoEscenario,
} from "@/lib/api";
import { versionMasReciente } from "@/lib/version";

export function Escenario() {
  const [elegido, setElegido] = useState<string | null>(null);
  const [prospecto, setProspecto] = useState<ProspectoEscenario | null>(null);

  const versiones = useQuery({ queryKey: clavesConsulta.versiones, queryFn: listarVersiones });
  const escenarios = useQuery({ queryKey: clavesConsulta.escenarios, queryFn: listarEscenarios });
  const version = versiones.data ? versionMasReciente(versiones.data) : undefined;

  const previsualizar = useMutation({
    mutationFn: (escenarioId: string) =>
      probarEscenario(version!.id, { escenario_id: escenarioId, aplicar: false }),
    onSuccess: (datos) => setProspecto(datos),
  });

  const aplicar = useMutation({
    mutationFn: (escenarioId: string) =>
      probarEscenario(version!.id, { escenario_id: escenarioId, aplicar: true }),
    onSuccess: (datos) => setProspecto(datos),
  });

  const ocupado = previsualizar.isPending || aplicar.isPending;
  const errores = prospecto?.conflictos.filter((item) => item.gravedad === "error") ?? [];

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Escenario
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          "¿Y si D2 no viene el martes?" Elegí un escenario, mirá el impacto antes de aplicarlo y
          recién ahí decidí. No se guarda nada hasta que confirmes.
        </p>
      </div>

      {versiones.isLoading || escenarios.isLoading ? <Cargando que="los escenarios" /> : null}
      {escenarios.isError ? <ErrorConsulta error={escenarios.error} /> : null}

      {!version && versiones.data ? (
        <Vacio titulo="Todavía no hay una versión de horario">
          Generá el horario desde <strong>Horario</strong> antes de probar un escenario.
        </Vacio>
      ) : null}

      {escenarios.data?.length === 0 ? (
        <Vacio titulo="No hay escenarios cargados">
          El Excel trae uno ("D2 sin clase el martes"). Si no aparece, revisá la hoja Cambio.
        </Vacio>
      ) : null}

      {version && escenarios.data && escenarios.data.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Escenarios disponibles</CardTitle>
            <CardDescription>
              Versión {version.numero} ·{" "}
              {version.escenario_id
                ? `escenario activo: ${
                    escenarios.data.find((item) => item.id === version.escenario_id)?.nombre ??
                    version.escenario_id
                  }`
                : "sin escenario aplicado"}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <ul className="flex flex-col gap-2">
              {escenarios.data.map((escenario) => (
                <li
                  key={escenario.id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-cell border border-mh-border px-4 py-3"
                >
                  <div>
                    <p className="text-label text-mh-text">{escenario.nombre}</p>
                    {escenario.descripcion ? (
                      <p className="text-body-sm text-mh-secondary">{escenario.descripcion}</p>
                    ) : null}
                  </div>
                  <Button
                    variant={elegido === escenario.id ? "default" : "outline"}
                    size="sm"
                    disabled={ocupado}
                    onClick={() => {
                      setElegido(escenario.id);
                      setProspecto(null);
                      previsualizar.mutate(escenario.id);
                    }}
                  >
                    <CalendarClock aria-hidden="true" />
                    {previsualizar.isPending && elegido === escenario.id
                      ? "Calculando…"
                      : "Ver impacto"}
                  </Button>
                </li>
              ))}
            </ul>
            <span aria-live="polite" className="text-label-xs text-mh-muted">
              {previsualizar.isPending ? "El solver está re-planificando. Puede tardar unos segundos." : ""}
            </span>
          </CardContent>
        </Card>
      ) : null}

      {prospecto ? (
        <Card>
          <CardHeader>
            <CardTitle>
              {prospecto.aplicado ? "Escenario aplicado" : "Impacto estimado"}
            </CardTitle>
            <CardDescription>
              {prospecto.escenario.nombre} · {prospecto.sesiones_afectadas} sesión(es) en franjas que
              dejan de estar disponibles
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <dl className="grid grid-cols-2 gap-4 text-body-sm md:grid-cols-4">
              <div>
                <dt className="text-mh-muted">Resultado</dt>
                <dd className="text-h3 text-mh-text">{prospecto.resultado.estado}</dd>
              </div>
              <div>
                <dt className="text-mh-muted">Sesiones</dt>
                <dd className="text-h3 text-mh-text">{prospecto.resultado.sesiones}</dd>
              </div>
              <div>
                <dt className="text-mh-muted">Afectadas</dt>
                <dd className="text-h3 text-mh-text">{prospecto.sesiones_afectadas}</dd>
              </div>
              <div>
                <dt className="text-mh-muted">Conflictos</dt>
                <dd className="text-h3 text-mh-text">{prospecto.conflictos.length}</dd>
              </div>
            </dl>

            {errores.length > 0 ? (
              <Aviso tono="error">
                <span className="block font-semibold">
                  {errores.length} conflictos quedarían abiertos
                </span>
                <ul className="mt-1 flex flex-col gap-1">
                  {errores.slice(0, 5).map((conflicto, indice) => (
                    <li key={`${conflicto.codigo}-${indice}`}>
                      · {conflicto.codigo}: {conflicto.mensaje}
                    </li>
                  ))}
                </ul>
              </Aviso>
            ) : (
              <Aviso tono="ok">
                <span className="flex items-center gap-2">
                  <CheckCircle2 aria-hidden="true" className="size-4" />
                  Sin errores: el horario quedaría publicable.
                </span>
              </Aviso>
            )}

            {prospecto.resultado.diagnostico.length > 0 ? (
              <Aviso tono="advertencia">
                <ul className="flex flex-col gap-1">
                  {prospecto.resultado.diagnostico.map((item, indice) => (
                    <li key={`${item.codigo}-${indice}`}>
                      <AlertTriangle aria-hidden="true" className="mr-1 inline size-3.5" />
                      {item.mensaje}
                    </li>
                  ))}
                </ul>
              </Aviso>
            ) : null}

            {prospecto.aplicado ? (
              <div className="flex flex-wrap gap-2">
                <Button asChild>
                  <Link to="/horario">Ver el horario re-planificado</Link>
                </Button>
                <Button variant="outline" asChild>
                  <Link to="/publicacion">Publicar</Link>
                </Button>
              </div>
            ) : (
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  onClick={() => elegido && aplicar.mutate(elegido)}
                  disabled={ocupado || !elegido}
                >
                  {aplicar.isPending ? "Aplicando…" : "Aplicar escenario"}
                </Button>
                <Button variant="outline" onClick={() => setProspecto(null)} disabled={ocupado}>
                  Descartar
                </Button>
                <span className="text-label-xs text-mh-muted">
                  Aplicar re-planifica la semana completa con el escenario activo.
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      ) : null}
    </section>
  );
}
