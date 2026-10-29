import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";

import { Aviso, Cargando, ErrorConsulta } from "@/components/estados";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  clavesConsulta,
  listarAsignaciones,
  listarConflictos,
  listarCursos,
  listarDocentes,
  listarRecursos,
  listarVersiones,
  vistaHorario,
} from "@/lib/api";
import { versionMasReciente } from "@/lib/version";

type Paso = { titulo: string; detalle: string; listo: boolean; ruta: string };

function Checklist({ pasos }: { pasos: Paso[] }) {
  return (
    <ol className="flex flex-col gap-2">
      {pasos.map((paso) => (
        <li
          key={paso.titulo}
          className="flex items-start gap-3 rounded-cell border border-mh-border px-4 py-3"
        >
          {paso.listo ? (
            <CheckCircle2 aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-mh-success" />
          ) : (
            <Circle aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-mh-muted" />
          )}
          <div className="flex-1">
            <p className="text-label text-mh-text">
              {paso.titulo}
              <span className="sr-only">{paso.listo ? " (completo)" : " (pendiente)"}</span>
            </p>
            <p className="text-body-sm text-mh-secondary">{paso.detalle}</p>
          </div>
          <Link
            to={paso.ruta}
            className="min-h-[44px] self-center rounded-sm border border-mh-border-control px-4 py-2 text-label-xs text-mh-text hover:bg-mh-raised"
          >
            Ir
          </Link>
        </li>
      ))}
    </ol>
  );
}

export function Inicio() {
  const cursos = useQuery({ queryKey: clavesConsulta.cursos, queryFn: listarCursos });
  const docentes = useQuery({ queryKey: clavesConsulta.docentes, queryFn: listarDocentes });
  const recursos = useQuery({ queryKey: clavesConsulta.recursos, queryFn: listarRecursos });
  const asignaciones = useQuery({
    queryKey: clavesConsulta.asignaciones,
    queryFn: listarAsignaciones,
  });
  const versiones = useQuery({ queryKey: clavesConsulta.versiones, queryFn: listarVersiones });

  const version = versiones.data ? versionMasReciente(versiones.data) : undefined;
  const sesiones = useQuery({
    queryKey: clavesConsulta.sesiones(version?.id ?? "sin-version"),
    queryFn: () => vistaHorario(version!.id),
    enabled: Boolean(version),
  });
  const conflictos = useQuery({
    queryKey: clavesConsulta.conflictos(version?.id ?? "sin-version"),
    queryFn: () => listarConflictos(version!.id),
    enabled: Boolean(version),
  });

  const consultas = [cursos, docentes, recursos, asignaciones, versiones, sesiones, conflictos];
  // `isPending` incluye las consultas deshabilitadas (sin versión): `isLoading` no.
  const cargando = consultas.some((consulta) => consulta.isLoading);
  const fallida = consultas.find((consulta) => consulta.isError);

  const totalSesiones = sesiones.data?.sesiones.length ?? 0;
  const errores = (conflictos.data?.conflictos ?? []).filter(
    (conflicto) => conflicto.gravedad === "error",
  ).length;
  const advertencias = (conflictos.data?.conflictos.length ?? 0) - errores;

  const pasos: Paso[] = [
    {
      titulo: "1. Importar el Excel",
      detalle:
        (cursos.data?.length ?? 0) > 0
          ? `${cursos.data?.length} cursos y ${docentes.data?.length} docentes cargados.`
          : "Subí el archivo de la escuela: trae cursos, docentes, carga y salones.",
      listo: (cursos.data?.length ?? 0) > 0 && (docentes.data?.length ?? 0) > 0,
      ruta: "/importar",
    },
    {
      titulo: "2. Revisar la carga académica",
      detalle:
        (asignaciones.data?.length ?? 0) > 0
          ? `${asignaciones.data?.length} asignaciones y ${recursos.data?.length} recursos.`
          : "Cada curso necesita sus asignaturas, docente principal y salón.",
      listo: (asignaciones.data?.length ?? 0) > 0,
      ruta: "/cursos",
    },
    {
      titulo: "3. Generar el horario",
      detalle:
        totalSesiones > 0
          ? `${totalSesiones} sesiones colocadas en la versión ${version?.numero}.`
          : "El solver arma la semana sin solapamientos.",
      listo: totalSesiones > 0,
      ruta: "/horario",
    },
    {
      titulo: "4. Publicar",
      detalle:
        version?.estado === "publicado"
          ? "La versión está publicada."
          : "Se publica cuando no quedan errores.",
      listo: version?.estado === "publicado",
      ruta: "/publicacion",
    },
  ];

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Inicio
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          Hourly arma el horario escolar sin solapamientos: importa el Excel, audita los conflictos,
          genera el horario y publícalo.
        </p>
      </div>

      {cargando ? <Cargando que="el estado del horario" /> : null}
      {fallida ? (
        <ErrorConsulta error={fallida.error} onReintentar={() => void fallida.refetch()} />
      ) : null}

      {!cargando && !fallida ? (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Semáforo del horario</CardTitle>
                <CardDescription>
                  {version
                    ? `Versión ${version.numero} · ${version.estado}`
                    : "Todavía no hay una versión de horario."}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {!version ? (
                  <Aviso tono="info">Creá una versión desde Horario después de importar.</Aviso>
                ) : errores > 0 ? (
                  <Aviso tono="error">
                    {errores} conflictos que impiden publicar.{" "}
                    <Link className="underline" to="/conflictos">
                      Ver conflictos
                    </Link>
                  </Aviso>
                ) : advertencias > 0 ? (
                  <Aviso tono="advertencia">
                    {advertencias} advertencias, ninguna bloqueante.{" "}
                    <Link className="underline" to="/conflictos">
                      Revisarlas
                    </Link>
                  </Aviso>
                ) : (
                  <Aviso tono="ok">
                    Sin conflictos:{" "}
                    {totalSesiones > 0
                      ? "el horario se puede publicar."
                      : "falta generar el horario."}
                  </Aviso>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Resumen</CardTitle>
                <CardDescription>Lo que hay cargado hoy.</CardDescription>
              </CardHeader>
              <CardContent>
                <dl className="grid grid-cols-2 gap-4 text-body-sm">
                  {[
                    ["Cursos", cursos.data?.length ?? 0],
                    ["Docentes", docentes.data?.length ?? 0],
                    ["Recursos", recursos.data?.length ?? 0],
                    ["Asignaciones", asignaciones.data?.length ?? 0],
                  ].map(([etiqueta, valor]) => (
                    <div key={String(etiqueta)}>
                      <dt className="text-mh-muted">{etiqueta}</dt>
                      <dd className="text-h3 text-mh-text">{valor}</dd>
                    </div>
                  ))}
                </dl>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Configuración</CardTitle>
              <CardDescription>Los cuatro pasos para tener un horario publicado.</CardDescription>
            </CardHeader>
            <CardContent>
              <Checklist pasos={pasos} />
            </CardContent>
          </Card>

          <p className="flex items-center gap-2 text-label-xs text-mh-muted">
            <Loader2 aria-hidden="true" className="size-3.5" />
            La grilla interactiva llega en la fase 7 y las propuestas de IA en la fase 8.
          </p>
        </>
      ) : null}
    </section>
  );
}
