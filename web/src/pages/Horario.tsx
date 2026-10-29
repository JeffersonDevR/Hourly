import {
  DndContext,
  useDraggable,
  useDroppable,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  CalendarPlus,
  CheckCircle2,
  GitBranch,
  GripVertical,
  Pin,
  Redo2,
  Undo2,
} from "lucide-react";
import { useMemo, useState } from "react";
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
  arrastre,
  clavesConsulta,
  colocarSesion,
  crearVersion,
  deshacerVersion,
  generarHorario,
  listarAsignaciones,
  listarAsignaturas,
  listarBloques,
  listarCursos,
  listarDocentes,
  listarRecursos,
  listarVersiones,
  moverSesion,
  quitarSesion,
  rehacerVersion,
  validarVersion,
  vistaHorario,
  type CeldaArrastre,
  ErrorApi,
} from "@/lib/api";
import { usaGrillaCompacta } from "@/lib/media";
import { cn } from "@/lib/utils";
import { versionMasReciente } from "@/lib/version";
import type { Asignacion, Bloque, Sesion } from "@/types/api";

const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"] as const;

type Vista = "curso" | "docente" | "recurso";

type ArrastreItem =
  | { id: string; tipo: "nueva"; asignacionId: string }
  | { id: string; tipo: "sesion"; sesionId: string; asignacionId: string };

const clave = (dia: number, bloqueId: string) => `${dia}:${bloqueId}`;

function Ficha({
  item,
  children,
  className,
}: {
  item: ArrastreItem;
  children: React.ReactNode;
  className?: string;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: item.id,
    data: item,
  });

  return (
    <div
      ref={setNodeRef}
      {...attributes}
      {...listeners}
      style={
        transform ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` } : undefined
      }
      className={cn(
        "cursor-grab touch-none rounded-cell border border-mh-border bg-mh-raised px-2 py-1.5 text-left text-label-xs text-mh-text",
        isDragging && "opacity-50",
        className,
      )}
    >
      {children}
    </div>
  );
}

function Celda({
  dia,
  bloqueId,
  estado,
  motivo,
  children,
}: {
  dia: number;
  bloqueId: string;
  estado: CeldaArrastre["estado"] | undefined;
  motivo?: string | null | undefined;
  children?: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: clave(dia, bloqueId) });

  return (
    <td
      ref={setNodeRef}
      title={motivo ?? undefined}
      className={cn(
        "h-[76px] border border-mh-border p-1 align-top",
        estado === "bloqueada" && "bg-mh-danger-surface",
        estado === "advertencia" && "bg-mh-warning-surface",
        estado === "valida" && "bg-mh-success-surface",
        isOver && "ring-2 ring-mh-accent",
      )}
    >
      {children}
      {estado === "bloqueada" || estado === "advertencia" ? (
        <p className="mt-1 flex items-center gap-1 text-label-xs">
          <AlertTriangle
            aria-hidden="true"
            className={cn("size-3.5", estado === "bloqueada" ? "text-mh-danger" : "text-mh-warning")}
          />
          <span className="text-mh-secondary">
            {estado === "bloqueada" ? "Bloqueada" : "Revisar"}
          </span>
          <span className="sr-only">{motivo}</span>
        </p>
      ) : null}
    </td>
  );
}

export function Horario() {
  const cliente = useQueryClient();

  const versiones = useQuery({ queryKey: clavesConsulta.versiones, queryFn: listarVersiones });
  const version = versiones.data ? versionMasReciente(versiones.data) : undefined;

  const bloques = useQuery({ queryKey: clavesConsulta.bloques, queryFn: listarBloques });
  const cursos = useQuery({ queryKey: clavesConsulta.cursos, queryFn: listarCursos });
  const docentes = useQuery({ queryKey: clavesConsulta.docentes, queryFn: listarDocentes });
  const recursos = useQuery({ queryKey: clavesConsulta.recursos, queryFn: listarRecursos });
  const asignaturas = useQuery({ queryKey: clavesConsulta.asignaturas, queryFn: listarAsignaturas });
  const asignaciones = useQuery({
    queryKey: clavesConsulta.asignaciones,
    queryFn: listarAsignaciones,
  });
  const sesiones = useQuery({
    queryKey: clavesConsulta.sesiones(version?.id ?? "sin-version"),
    queryFn: () => vistaHorario(version!.id),
    enabled: Boolean(version),
  });

  const [vista, setVista] = useState<Vista>("curso");
  const [idVista, setIdVista] = useState<string | null>(null);
  const [modo, setModo] = useState<"principal" | "habilitados">("habilitados");
  const [soloVista, setSoloVista] = useState(false);
  const [mensaje, setMensaje] = useState<{ tono: "ok" | "error" | "advertencia"; texto: string } | null>(
    null,
  );
  const [arrastrando, setArrastrando] = useState<ArrastreItem | null>(null);
  const [sesionElegida, setSesionElegida] = useState<string>("");
  const [diaDestino, setDiaDestino] = useState(1);
  const compacta = usaGrillaCompacta();
  const [diaVisible, setDiaVisible] = useState(1);
  const [bloqueDestino, setBloqueDestino] = useState("");

  const opcionesVista = vista === "curso" ? cursos.data : vista === "docente" ? docentes.data : recursos.data;
  const seleccionId = idVista ?? opcionesVista?.[0]?.id ?? null;

  // Todos los bloques, no solo las clases: los recreos y el almuerzo son parte del
  // horario de los estudiantes y tienen que verse en la grilla.
  const bloquesOrdenados = useMemo(
    () => [...(bloques.data ?? [])].sort((a, b) => a.orden - b.orden),
    [bloques.data],
  );
  const bloquesClase = useMemo(
    () => bloquesOrdenados.filter((bloque) => bloque.tipo === "clase"),
    [bloquesOrdenados],
  );
  const asignaturaPorId = useMemo(
    () => new Map((asignaturas.data ?? []).map((item) => [item.id, item])),
    [asignaturas.data],
  );
  const asignacionPorId = useMemo(
    () => new Map((asignaciones.data ?? []).map((item) => [item.id, item])),
    [asignaciones.data],
  );
  const cursoPorId = useMemo(
    () => new Map((cursos.data ?? []).map((item) => [item.id, item])),
    [cursos.data],
  );
  const docentePorId = useMemo(
    () => new Map((docentes.data ?? []).map((item) => [item.id, item])),
    [docentes.data],
  );
  const recursoPorId = useMemo(
    () => new Map((recursos.data ?? []).map((item) => [item.id, item])),
    [recursos.data],
  );

  // Abajo de 1024 la grilla no se comprime ni scrollea: se muestra un día (diseño §5).
  const diasVisibles = compacta ? [diaVisible] : [1, 2, 3, 4, 5];

  const todasLasSesiones = sesiones.data?.sesiones ?? [];

  const enVista = (sesion: Sesion) =>
    vista === "curso"
      ? sesion.curso_id === seleccionId
      : vista === "docente"
        ? sesion.docente_id === seleccionId
        : sesion.recurso_id === seleccionId;

  const sesionesVista = todasLasSesiones.filter(enVista);
  const porFranja = new Map(sesionesVista.map((sesion) => [clave(sesion.dia, sesion.bloque_id), sesion]));

  // --- pendientes de colocar, en el alcance de la vista ---
  const recursoElegido = vista === "recurso" ? recursoPorId.get(seleccionId ?? "") : undefined;
  const asignacionesVista = (asignaciones.data ?? []).filter((asignacion: Asignacion) =>
    vista === "curso"
      ? asignacion.curso_id === seleccionId
      : vista === "docente"
        ? asignacion.docente_principal_id === seleccionId
        : asignacion.tipo_recurso_requerido === recursoElegido?.tipo_recurso,
  );
  const colocadasPorAsignacion = new Map<string, number>();
  for (const sesion of todasLasSesiones) {
    colocadasPorAsignacion.set(
      sesion.asignacion_carga_id,
      (colocadasPorAsignacion.get(sesion.asignacion_carga_id) ?? 0) + 1,
    );
  }
  const pendientes = asignacionesVista
    .map((asignacion) => ({
      asignacion,
      faltan: asignacion.sesiones_semana - (colocadasPorAsignacion.get(asignacion.id) ?? 0),
    }))
    .filter((item) => item.faltan > 0);

  const totalPedidas = asignacionesVista.reduce((suma, item) => suma + item.sesiones_semana, 0);
  const totalColocadas = asignacionesVista.reduce(
    (suma, item) => suma + (colocadasPorAsignacion.get(item.id) ?? 0),
    0,
  );

  // --- pintado de celdas al arrastrar (endpoint de la fase 5) ---
  const mapaArrastre = useQuery({
    queryKey: clavesConsulta.arrastre(version?.id ?? "", arrastrando?.asignacionId ?? ""),
    queryFn: () => arrastre(version!.id, arrastrando!.asignacionId),
    enabled: Boolean(version && arrastrando),
  });
  const estadosCelda = new Map(
    (mapaArrastre.data?.celdas ?? []).map((celda) => [clave(celda.dia, celda.bloque_id), celda]),
  );

  const avisarError = (error: unknown) =>
    setMensaje({
      tono: "error",
      texto:
        error instanceof ErrorApi
          ? `${error.codigo}: ${error.message}`
          : "No se pudo completar el cambio.",
    });

  const refrescar = async () => {
    if (!version) return;
    // El semáforo depende de los conflictos: se recalculan tras cada cambio.
    await validarVersion(version.id);
    void cliente.invalidateQueries({ queryKey: clavesConsulta.sesiones(version.id) });
    void cliente.invalidateQueries({ queryKey: clavesConsulta.conflictos(version.id) });
    void cliente.invalidateQueries({ queryKey: clavesConsulta.versiones });
  };

  const nuevaVersion = useMutation({
    mutationFn: (datos: { copiar_de?: string } = {}) => crearVersion(datos),
    onSuccess: (creada, datos) => {
      cliente.setQueryData(clavesConsulta.versiones, (previas: typeof versiones.data) => [
        ...(previas ?? []),
        creada,
      ]);
      setMensaje({
        tono: "ok",
        texto: datos.copiar_de
          ? `Versión ${creada.numero} creada como copia en borrador. La anterior no se tocó.`
          : `Versión ${creada.numero} creada en borrador.`,
      });
    },
    onError: avisarError,
  });

  const colocar = useMutation({
    mutationFn: (datos: { asignacionId: string; dia: number; bloqueId: string }) =>
      colocarSesion(version!.id, {
        asignacion_carga_id: datos.asignacionId,
        dia: datos.dia,
        bloque_id: datos.bloqueId,
        ...(vista === "docente" && seleccionId ? { docente_id: seleccionId } : {}),
        ...(vista === "recurso" && seleccionId ? { recurso_id: seleccionId } : {}),
      }),
    onSuccess: async () => {
      setMensaje({ tono: "ok", texto: "Sesión colocada." });
      await refrescar();
    },
    onError: avisarError,
  });

  const mover = useMutation({
    mutationFn: (datos: { sesionId: string; dia: number; bloqueId: string }) =>
      moverSesion(version!.id, datos.sesionId, { dia: datos.dia, bloque_id: datos.bloqueId }),
    onSuccess: async () => {
      setMensaje({ tono: "ok", texto: "Sesión movida." });
      await refrescar();
    },
    onError: avisarError,
  });

  const fijar = useMutation({
    mutationFn: (datos: { sesionId: string; fijada: boolean }) =>
      moverSesion(version!.id, datos.sesionId, { fijada: datos.fijada }),
    onSuccess: async (_datos, variables) => {
      setMensaje({
        tono: "ok",
        texto: variables.fijada
          ? "Sesión fijada: generar no la va a mover."
          : "Sesión liberada: generar puede moverla.",
      });
      await refrescar();
    },
    onError: avisarError,
  });

  const quitar = useMutation({
    mutationFn: (sesionId: string) => quitarSesion(version!.id, sesionId),
    onSuccess: async () => {
      setMensaje({ tono: "ok", texto: "Sesión quitada." });
      setSesionElegida("");
      await refrescar();
    },
    onError: avisarError,
  });

  const deshacer = useMutation({
    mutationFn: () => deshacerVersion(version!.id),
    onSuccess: async () => {
      setMensaje({ tono: "ok", texto: "Deshecho." });
      await refrescar();
    },
    onError: avisarError,
  });

  const rehacer = useMutation({
    mutationFn: () => rehacerVersion(version!.id),
    onSuccess: async () => {
      setMensaje({ tono: "ok", texto: "Rehecho." });
      await refrescar();
    },
    onError: avisarError,
  });

  const generar = useMutation({
    mutationFn: () =>
      generarHorario(version!.id, {
        modo_docente: modo,
        solo_curso_id: soloVista && vista === "curso" ? seleccionId : null,
      }),
    onSuccess: async (resultado) => {
      setMensaje({
        tono: resultado.estado === "INFACTIBLE" || resultado.estado === "TIMEOUT" ? "error" : "ok",
        texto:
          resultado.diagnostico.length > 0
            ? `${resultado.estado}: ${resultado.diagnostico.map((item) => item.mensaje).join(" ")}`
            : `${resultado.estado} · ${resultado.sesiones} sesiones en ${
                resultado.objetivo === null ? "sin objetivo" : `objetivo ${resultado.objetivo}`
              }.`,
      });
      void cliente.invalidateQueries({ queryKey: clavesConsulta.sesiones(version!.id) });
      void cliente.invalidateQueries({ queryKey: clavesConsulta.conflictos(version!.id) });
      void cliente.invalidateQueries({ queryKey: clavesConsulta.versiones });
    },
    onError: avisarError,
  });

  const onDragStart = (evento: DragStartEvent) => {
    const item = evento.active.data.current as ArrastreItem | undefined;
    setArrastrando(item ?? null);
    setMensaje(null);
  };

  const onDragEnd = (evento: DragEndEvent) => {
    const item = evento.active.data.current as ArrastreItem | undefined;
    setArrastrando(null);
    if (!item || !evento.over || !version) return;

    const [diaTexto, bloqueId] = String(evento.over.id).split(":");
    const dia = Number(diaTexto);
    if (!dia || !bloqueId) return;

    const info = estadosCelda.get(clave(dia, bloqueId));
    if (!info) {
      setMensaje({ tono: "advertencia", texto: "Esperá a que termine de calcular las celdas." });
      return;
    }
    if (info.estado === "bloqueada") {
      setMensaje({ tono: "error", texto: info.motivo ?? "Esa franja está bloqueada." });
      return;
    }
    if (item.tipo === "nueva") {
      colocar.mutate({ asignacionId: item.asignacionId, dia, bloqueId });
    } else {
      mover.mutate({ sesionId: item.sesionId, dia, bloqueId });
    }
  };

  const cargando =
    versiones.isLoading ||
    bloques.isLoading ||
    cursos.isLoading ||
    docentes.isLoading ||
    asignaturas.isLoading ||
    asignaciones.isLoading ||
    recursos.isLoading ||
    Boolean(version) && sesiones.isLoading;
  const fallida = [versiones, bloques, cursos, docentes, recursos, asignaturas, asignaciones].find(
    (consulta) => consulta.isError,
  );

  const etiquetaAsignatura = (asignacionId: string) => {
    const asignacion = asignacionPorId.get(asignacionId);
    const asignatura = asignacion ? asignaturaPorId.get(asignacion.asignatura_id) : undefined;
    return asignatura?.nombre ?? "Asignatura";
  };
  const colorAsignatura = (asignacionId: string) => {
    const asignacion = asignacionPorId.get(asignacionId);
    const color = asignacion ? asignaturaPorId.get(asignacion.asignatura_id)?.color : undefined;
    return color ?? "var(--mh-border-control)";
  };

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
            Horario
          </h1>
          <p className="max-w-[70ch] text-body text-mh-secondary">
            Arrastrá una sesión a otra franja o una asignatura pendiente desde “Por colocar”. Las
            celdas se pintan con el motivo: bloqueada, con advertencia o válida.
          </p>
        </div>

        {version ? (
          <div className="flex flex-wrap items-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => deshacer.mutate()}
              disabled={deshacer.isPending}
            >
              <Undo2 aria-hidden="true" />
              Deshacer
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => rehacer.mutate()}
              disabled={rehacer.isPending}
            >
              <Redo2 aria-hidden="true" />
              Rehacer
            </Button>
            <Button variant="outline" size="sm" asChild>
              <Link to="/escenario">
                <GitBranch aria-hidden="true" />
                Probar escenario
              </Link>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => nuevaVersion.mutate({ copiar_de: version.id })}
              disabled={nuevaVersion.isPending}
            >
              <CalendarPlus aria-hidden="true" />
              Nueva versión desde esta
            </Button>
          </div>
        ) : null}
      </div>

      {cargando ? <Cargando que="el horario" /> : null}
      {fallida ? <ErrorConsulta error={fallida.error} onReintentar={() => void fallida.refetch()} /> : null}

      {mensaje ? (
        <div aria-live="polite">
          <Aviso tono={mensaje.tono}>{mensaje.texto}</Aviso>
        </div>
      ) : null}

      {!version && versiones.data ? (
        <Card>
          <CardHeader>
            <CardTitle>Sin versión de horario</CardTitle>
            <CardDescription>
              Una versión es la plantilla semanal que se edita y después se publica.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => nuevaVersion.mutate({})} disabled={nuevaVersion.isPending}>
              <CalendarPlus aria-hidden="true" />
              Crear versión en borrador
            </Button>
          </CardContent>
        </Card>
      ) : null}

      {version ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Generar</CardTitle>
              <CardDescription>
                Versión {version.numero} · {version.estado}. Con docentes principales el Excel real
                es infactible (D4 demanda 28 contra un máximo de 24): es el caso que la demo muestra.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-end gap-3">
              <label className="flex flex-col gap-1 text-label-xs text-mh-secondary">
                Docentes
                <select
                  value={modo}
                  onChange={(evento) =>
                    setModo(evento.target.value === "principal" ? "principal" : "habilitados")
                  }
                  className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-3 text-body-sm text-mh-text"
                >
                  <option value="habilitados">Habilitados</option>
                  <option value="principal">Solo principales</option>
                </select>
              </label>

              <label className="flex min-h-[44px] items-center gap-2 text-label-xs text-mh-secondary">
                <input
                  type="checkbox"
                  checked={soloVista}
                  disabled={vista !== "curso"}
                  onChange={(evento) => setSoloVista(evento.target.checked)}
                  className="size-5 accent-[var(--mh-accent)]"
                />
                Solo esta vista
                {vista !== "curso" ? <span className="text-mh-muted">(elegí un curso)</span> : null}
              </label>

              <Button onClick={() => generar.mutate()} disabled={generar.isPending}>
                {generar.isPending ? "Generando…" : "Generar horario"}
              </Button>

              <span aria-live="polite" className="text-label-xs text-mh-muted">
                {generar.isPending ? "El solver está trabajando, puede tardar unos segundos." : ""}
              </span>
            </CardContent>
          </Card>

          <div className="grid gap-4 xl:grid-cols-[1fr_320px]">
            <Card>
              <CardHeader className="flex flex-row items-end justify-between gap-3 pb-0">
                <div className="flex flex-col gap-1">
                  <CardTitle>Grilla semanal</CardTitle>
                  <CardDescription>
                    {totalColocadas} de {totalPedidas} sesiones colocadas en esta vista
                  </CardDescription>
                </div>
                <div className="flex flex-wrap items-end gap-2">
                  <label className="flex flex-col gap-1 text-label-xs text-mh-secondary">
                    Vista
                    <select
                      value={vista}
                      onChange={(evento) => {
                        const siguiente = evento.target.value;
                        setVista(siguiente === "docente" || siguiente === "recurso" ? siguiente : "curso");
                        setIdVista(null);
                        setSoloVista(false);
                      }}
                      className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-3 text-body-sm text-mh-text"
                    >
                      <option value="curso">Curso</option>
                      <option value="docente">Docente</option>
                      <option value="recurso">Aula</option>
                    </select>
                  </label>
                  <label className="flex flex-col gap-1 text-label-xs text-mh-secondary">
                    {vista === "curso" ? "Curso" : vista === "docente" ? "Docente" : "Recurso"}
                    <select
                      value={seleccionId ?? ""}
                      onChange={(evento) => setIdVista(evento.target.value)}
                      className="min-h-[44px] max-w-[220px] rounded-sm border border-mh-border-control bg-mh-canvas px-3 text-body-sm text-mh-text"
                    >
                      {(opcionesVista ?? []).map((opcion) => (
                        <option key={opcion.id} value={opcion.id}>
                          {`${opcion.codigo} · ${opcion.nombre}`}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              </CardHeader>

              <CardContent>
                {!seleccionId ? (
                  <Vacio titulo="No hay datos para esta vista">
                    Importá el Excel o creá los catálogos primero.
                  </Vacio>
                ) : (
                  <DndContext onDragStart={onDragStart} onDragEnd={onDragEnd}>
                    {compacta ? (
                      <div className="mb-3 flex flex-wrap items-center gap-2">
                        <span className="text-label-xs text-mh-secondary">Día</span>
                        {DIAS.map((dia, indice) => (
                          <button
                            key={dia}
                            type="button"
                            aria-pressed={diaVisible === indice + 1}
                            onClick={() => setDiaVisible(indice + 1)}
                            className={cn(
                              "min-h-[44px] rounded-full border px-4 text-label-xs",
                              diaVisible === indice + 1
                                ? "border-mh-text bg-mh-raised text-mh-text"
                                : "border-mh-border text-mh-secondary hover:bg-mh-raised",
                            )}
                          >
                            {dia}
                          </button>
                        ))}
                      </div>
                    ) : null}
                    <div className="mh-scroll-x">
                      <table className="w-full border-collapse text-label-xs">
                        <caption className="sr-only">
                          Horario semanal por {vista}, con celdas arrastrables
                        </caption>
                        <thead>
                          <tr>
                            <th scope="col" className="w-[88px] p-2 text-left text-mh-muted">
                              Bloque
                            </th>
                            {diasVisibles.map((numeroDia) => (
                              <th
                                key={numeroDia}
                                scope="col"
                                className="p-2 text-left text-mh-muted"
                              >
                                {DIAS[numeroDia - 1]}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {bloquesOrdenados.map((bloque: Bloque) =>
                            bloque.tipo !== "clase" ? (
                              <tr key={bloque.id}>
                                <th
                                  scope="row"
                                  className="p-2 text-left align-middle text-mh-muted"
                                >
                                  {bloque.codigo}
                                </th>
                                <td
                                  colSpan={diasVisibles.length}
                                  className="border border-mh-border bg-mh-sunken px-3 py-2 text-label-xs text-mh-muted"
                                >
                                  {bloque.tipo === "almuerzo" ? "Almuerzo" : "Recreo"},{" "}
                                  de {bloque.inicio.slice(0, 5)} a {bloque.fin.slice(0, 5)}. Sin
                                  sesiones
                                </td>
                              </tr>
                            ) : (
                            <tr key={bloque.id}>
                              <th scope="row" className="p-2 text-left align-top text-mh-secondary">
                                <span className="block text-mh-text">{bloque.codigo}</span>
                                <span className="text-mh-muted">
                                  {bloque.inicio.slice(0, 5)} a {bloque.fin.slice(0, 5)}
                                </span>
                              </th>
                              {diasVisibles.map((numeroDia) => {
                                const sesion = porFranja.get(clave(numeroDia, bloque.id));
                                const info = estadosCelda.get(clave(numeroDia, bloque.id));

                                return (
                                  <Celda
                                    key={`${numeroDia}-${bloque.id}`}
                                    dia={numeroDia}
                                    bloqueId={bloque.id}
                                    estado={arrastrando ? info?.estado : undefined}
                                    motivo={info?.motivo}
                                  >
                                    {sesion ? (
                                      <Ficha
                                        item={{
                                          id: `sesion:${sesion.id}`,
                                          tipo: "sesion",
                                          sesionId: sesion.id,
                                          asignacionId: sesion.asignacion_carga_id,
                                        }}
                                        className="border-l-4"
                                      >
                                        <span
                                          aria-hidden="true"
                                          className="mb-1 block h-1 w-full rounded-full"
                                          style={{ backgroundColor: colorAsignatura(sesion.asignacion_carga_id) }}
                                        />
                                        <span className="flex items-center gap-1 font-semibold">
                                          {sesion.fijada ? (
                                            <Pin
                                              aria-hidden="true"
                                              className="size-3.5 shrink-0 text-mh-accent"
                                            />
                                          ) : null}
                                          {etiquetaAsignatura(sesion.asignacion_carga_id)}
                                          {sesion.fijada ? (
                                            <span className="sr-only">(fijada)</span>
                                          ) : null}
                                        </span>
                                        <span className="block text-mh-muted">
                                          {vista === "curso"
                                            ? (docentePorId.get(sesion.docente_id)?.codigo ?? "—")
                                            : (cursoPorId.get(sesion.curso_id)?.codigo ?? "—")}
                                          {" · "}
                                          {sesion.recurso_id
                                            ? (recursoPorId.get(sesion.recurso_id)?.codigo ?? "—")
                                            : "sin aula"}
                                        </span>
                                      </Ficha>
                                    ) : (
                                      <span className="text-mh-muted">libre</span>
                                    )}
                                  </Celda>
                                );
                              })}
                            </tr>
                            ),
                          )}
                        </tbody>
                      </table>
                    </div>
                  </DndContext>
                )}
              </CardContent>
            </Card>

            <div className="flex flex-col gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Por colocar</CardTitle>
                  <CardDescription>
                    Arrastrá al horario. Faltan {pendientes.reduce((suma, item) => suma + item.faltan, 0)}.
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-2">
                  {pendientes.length === 0 ? (
                    <Aviso tono="ok">
                      <span className="flex items-center gap-2">
                        <CheckCircle2 aria-hidden="true" className="size-4" />
                        La malla de esta vista está completa.
                      </span>
                    </Aviso>
                  ) : (
                    pendientes.map(({ asignacion, faltan }) => (
                      <Ficha
                        key={asignacion.id}
                        item={{
                          id: `nueva:${asignacion.id}`,
                          tipo: "nueva",
                          asignacionId: asignacion.id,
                        }}
                        className="flex items-center justify-between gap-2"
                      >
                        <span className="flex items-center gap-2">
                          <GripVertical aria-hidden="true" className="size-4 text-mh-muted" />
                          <span>
                            <span className="block font-semibold">
                              {etiquetaAsignatura(asignacion.id)}
                            </span>
                            <span className="block text-mh-muted">
                              {cursoPorId.get(asignacion.curso_id)?.codigo ?? "—"}
                            </span>
                          </span>
                        </span>
                        <span className="rounded-full border border-mh-border px-2 py-0.5">
                          faltan {faltan}
                        </span>
                      </Ficha>
                    ))
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Mover sin mouse</CardTitle>
                  <CardDescription>La misma operación con teclado.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col gap-2">
                  <label className="flex flex-col gap-1 text-label-xs text-mh-secondary">
                    Sesión
                    <select
                      value={sesionElegida}
                      onChange={(evento) => setSesionElegida(evento.target.value)}
                      className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-2 text-body-sm text-mh-text"
                    >
                      <option value="">Elegí una sesión…</option>
                      {sesionesVista.map((sesion) => (
                        <option key={sesion.id} value={sesion.id}>
                          {etiquetaAsignatura(sesion.asignacion_carga_id)} ·{" "}
                          {DIAS[sesion.dia - 1]} {bloquesClase.find((b) => b.id === sesion.bloque_id)?.codigo}
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="flex gap-2">
                    <label className="flex flex-1 flex-col gap-1 text-label-xs text-mh-secondary">
                      Día
                      <select
                        value={diaDestino}
                        onChange={(evento) => setDiaDestino(Number(evento.target.value))}
                        className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-2 text-body-sm text-mh-text"
                      >
                        {DIAS.map((dia, indice) => (
                          <option key={dia} value={indice + 1}>
                            {dia}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="flex flex-1 flex-col gap-1 text-label-xs text-mh-secondary">
                      Bloque
                      <select
                        value={bloqueDestino || (bloquesClase[0]?.id ?? "")}
                        onChange={(evento) => setBloqueDestino(evento.target.value)}
                        className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-2 text-body-sm text-mh-text"
                      >
                        {bloquesClase.map((bloque) => (
                          <option key={bloque.id} value={bloque.id}>
                            {bloque.codigo}
                          </option>
                        ))}
                      </select>
                    </label>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => {
                        const bloqueId = bloqueDestino || bloquesClase[0]?.id;
                        if (!sesionElegida || !bloqueId) return;
                        mover.mutate({ sesionId: sesionElegida, dia: diaDestino, bloqueId });
                      }}
                      disabled={!sesionElegida || mover.isPending}
                    >
                      Mover
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => sesionElegida && quitar.mutate(sesionElegida)}
                      disabled={!sesionElegida || quitar.isPending}
                    >
                      Quitar
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const elegida = sesionesVista.find((item) => item.id === sesionElegida);
                        if (!elegida) return;
                        fijar.mutate({ sesionId: elegida.id, fijada: !elegida.fijada });
                      }}
                      disabled={!sesionElegida || fijar.isPending}
                    >
                      <Pin aria-hidden="true" />
                      {sesionesVista.find((item) => item.id === sesionElegida)?.fijada
                        ? "Liberar"
                        : "Fijar"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
