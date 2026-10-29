import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Download, FileSpreadsheet, FileText, Send } from "lucide-react";
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
  listarConflictos,
  listarCursos,
  listarDocentes,
  listarRecursos,
  crearVersion,
  listarVersiones,
  publicarVersion,
  urlExportar,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { versionMasReciente } from "@/lib/version";

type Alcance = "general" | "curso" | "docente" | "recurso";

export function Publicacion() {
  const cliente = useQueryClient();
  const [alcance, setAlcance] = useState<Alcance>("general");
  const [objetivo, setObjetivo] = useState<string>("");
  const [aviso, setAviso] = useState<{ tono: "ok" | "error" | "advertencia"; texto: string } | null>(
    null,
  );

  const versiones = useQuery({ queryKey: clavesConsulta.versiones, queryFn: listarVersiones });
  const version = versiones.data ? versionMasReciente(versiones.data) : undefined;
  const conflictos = useQuery({
    queryKey: clavesConsulta.conflictos(version?.id ?? "sin-version"),
    queryFn: () => listarConflictos(version!.id),
    enabled: Boolean(version),
  });
  const cursos = useQuery({ queryKey: clavesConsulta.cursos, queryFn: listarCursos });
  const docentes = useQuery({ queryKey: clavesConsulta.docentes, queryFn: listarDocentes });
  const recursos = useQuery({ queryKey: clavesConsulta.recursos, queryFn: listarRecursos });

  const lista = conflictos.data?.conflictos ?? [];
  const errores = lista.filter((conflicto) => conflicto.gravedad === "error");
  const advertencias = lista.length - errores.length;

  const publicar = useMutation({
    mutationFn: () => publicarVersion(version!.id),
    onSuccess: (publicada) => {
      setAviso({ tono: "ok", texto: `Versión ${publicada.numero} publicada.` });
      void cliente.invalidateQueries({ queryKey: clavesConsulta.versiones });
    },
    onError: (error) => {
      const detalle =
        error instanceof Error ? error.message : "No se pudo publicar la versión.";
      setAviso({ tono: "error", texto: detalle });
    },
  });

  const clonar = useMutation({
    mutationFn: (origen: string) => crearVersion({ copiar_de: origen }),
    onSuccess: (creada) => {
      setAviso({
        tono: "ok",
        texto: `Versión ${creada.numero} creada en borrador. Editá esa, la publicada queda como está.`,
      });
      void cliente.invalidateQueries({ queryKey: clavesConsulta.versiones });
    },
    onError: () => setAviso({ tono: "error", texto: "No se pudo crear el borrador." }),
  });

  const opciones =
    alcance === "curso"
      ? (cursos.data ?? []).map((item) => ({ id: item.id, etiqueta: `${item.codigo} · ${item.nombre}` }))
      : alcance === "docente"
        ? (docentes.data ?? []).map((item) => ({ id: item.id, etiqueta: `${item.codigo} · ${item.nombre}` }))
        : alcance === "recurso"
          ? (recursos.data ?? []).map((item) => ({ id: item.id, etiqueta: `${item.codigo} · ${item.nombre}` }))
          : [];

  const idAlcance = alcance === "general" ? "" : objetivo || (opciones[0]?.id ?? "");
  const enlace = (formato: "xlsx" | "pdf") =>
    version
      ? `${urlExportar(version.id, alcance, formato)}${idAlcance ? `&id=${idAlcance}` : ""}`
      : "#";

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Publicar
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          Se publica una versión sin errores. Después queda como plantilla de la semana y se exporta
          para la escuela.
        </p>
      </div>

      {versiones.isLoading || conflictos.isLoading ? <Cargando que="la versión" /> : null}
      {conflictos.isError ? <ErrorConsulta error={conflictos.error} /> : null}

      {aviso ? (
        <div aria-live="polite">
          <Aviso tono={aviso.tono}>{aviso.texto}</Aviso>
        </div>
      ) : null}

      {!version && versiones.data ? (
        <Vacio titulo="Todavía no hay una versión">
          Creá una desde <strong>Horario</strong> y generá el horario.
        </Vacio>
      ) : null}

      {version ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Validación</CardTitle>
              <CardDescription>
                Versión {version.numero} · {version.estado}
                {version.publicado_at ? ` · publicada el ${version.publicado_at.slice(0, 10)}` : ""}
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              {errores.length > 0 ? (
                <Aviso tono="error">
                  <span className="block font-semibold">
                    {errores.length} errores impiden publicar
                  </span>
                  <ul className="mt-1 flex flex-col gap-1">
                    {errores.slice(0, 5).map((conflicto, indice) => (
                      <li key={`${conflicto.codigo}-${indice}`}>
                        · {conflicto.codigo}: {conflicto.mensaje}
                      </li>
                    ))}
                  </ul>
                  <Link className="mt-2 inline-block underline" to="/conflictos">
                    Resolver en Conflictos
                  </Link>
                </Aviso>
              ) : (
                <Aviso tono="ok">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 aria-hidden="true" className="size-4" />
                    Sin errores. {advertencias} advertencia(s) no bloquean la publicación.
                  </span>
                </Aviso>
              )}

              <div className="flex flex-wrap items-center gap-3">
                <Button
                  onClick={() => publicar.mutate()}
                  disabled={publicar.isPending || errores.length > 0}
                >
                  <Send aria-hidden="true" />
                  {publicar.isPending ? "Publicando…" : "Publicar versión"}
                </Button>
                {version.estado === "publicado" ? (
                  <>
                    <span className="flex items-center gap-2 text-label-xs text-mh-success">
                      <CheckCircle2 aria-hidden="true" className="size-4" />
                      Ya está publicada: no se puede editar (D-021)
                    </span>
                    <Button variant="outline" onClick={() => clonar.mutate(version.id)}>
                      {clonar.isPending ? "Creando…" : "Crear borrador desde esta"}
                    </Button>
                  </>
                ) : null}
              </div>
              {errores.length > 0 ? (
                <p className="flex items-center gap-2 text-label-xs text-mh-muted">
                  <AlertTriangle aria-hidden="true" className="size-3.5" />
                  El botón se habilita cuando no quedan errores.
                </p>
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Exportar</CardTitle>
              <CardDescription>Excel para editar, PDF para imprimir y pegar en la pared.</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-end gap-3">
              <label className="flex flex-col gap-1 text-label-xs text-mh-secondary">
                Alcance
                <select
                  value={alcance}
                  onChange={(evento) => {
                    setAlcance(evento.target.value as Alcance);
                    setObjetivo("");
                  }}
                  className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-3 text-body-sm text-mh-text"
                >
                  <option value="general">Todos los cursos</option>
                  <option value="curso">Un curso</option>
                  <option value="docente">Un docente</option>
                  <option value="recurso">Un aula</option>
                </select>
              </label>

              {alcance !== "general" ? (
                <label className="flex flex-col gap-1 text-label-xs text-mh-secondary">
                  {alcance === "curso" ? "Curso" : alcance === "docente" ? "Docente" : "Aula"}
                  <select
                    value={idAlcance}
                    onChange={(evento) => setObjetivo(evento.target.value)}
                    className="min-h-[44px] max-w-[240px] rounded-sm border border-mh-border-control bg-mh-canvas px-3 text-body-sm text-mh-text"
                  >
                    {opciones.map((opcion) => (
                      <option key={opcion.id} value={opcion.id}>
                        {opcion.etiqueta}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}

              <a
                href={enlace("xlsx")}
                className={cn(
                  "inline-flex min-h-[48px] items-center gap-2 rounded-sm border border-mh-border-control px-4 text-label text-mh-text hover:bg-mh-raised",
                  !idAlcance && alcance !== "general" && "pointer-events-none opacity-50",
                )}
              >
                <FileSpreadsheet aria-hidden="true" className="size-4" />
                Excel
              </a>
              <a
                href={enlace("pdf")}
                className={cn(
                  "inline-flex min-h-[48px] items-center gap-2 rounded-sm border border-mh-border-control px-4 text-label text-mh-text hover:bg-mh-raised",
                  !idAlcance && alcance !== "general" && "pointer-events-none opacity-50",
                )}
              >
                <FileText aria-hidden="true" className="size-4" />
                PDF
              </a>

              <span className="flex items-center gap-1.5 text-label-xs text-mh-muted">
                <Download aria-hidden="true" className="size-3.5" />
                Se descarga directo del backend.
              </span>
            </CardContent>
          </Card>
        </>
      ) : null}
    </section>
  );
}
