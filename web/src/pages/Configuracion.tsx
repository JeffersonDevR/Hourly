import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { useState, type ReactNode } from "react";

import { Aviso, Cargando, Vacio } from "@/components/estados";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  borrar,
  clavesConsulta,
  crearAptitud,
  crearAsignacion,
  crearAsignatura,
  crearBloque,
  crearCurso,
  crearDocente,
  crearGrado,
  crearRecurso,
  crearTipoRecurso,
  listarAptitudes,
  listarAsignaciones,
  listarAsignaturas,
  listarBloques,
  listarCursos,
  listarDocentes,
  listarGrados,
  listarRecursos,
  listarTiposRecurso,
} from "@/lib/api";
import { leerToken } from "@/lib/tokens";
import { cn } from "@/lib/utils";

type Opcion = { valor: string; etiqueta: string };

/** El color por defecto de una asignatura sale del acento del sistema, no de un literal. */
const colorPorDefecto = () => leerToken("--mh-accent");

type Campo =
  | { tipo: "texto"; clave: string; etiqueta: string; defecto?: string; requerido?: boolean }
  | { tipo: "hora"; clave: string; etiqueta: string; defecto?: string }
  | { tipo: "numero"; clave: string; etiqueta: string; defecto?: number; min?: number }
  | { tipo: "opcion"; clave: string; etiqueta: string; opciones: Opcion[] }
  | { tipo: "bool"; clave: string; etiqueta: string; defecto?: boolean };

type Fila = Record<string, unknown>;
type Valor = string | number | boolean;

function valorInicial(campo: Campo): Valor {
  if (campo.tipo === "bool") return campo.defecto ?? false;
  if (campo.tipo === "numero") return campo.defecto ?? 0;
  if (campo.tipo === "opcion") return campo.opciones[0]?.valor ?? "";
  return campo.defecto ?? "";
}

function aEnviar(campos: Campo[], valores: Record<string, Valor>): Fila {
  const salida: Fila = {};
  for (const campo of campos) {
    const valor = valores[campo.clave];
    if (campo.tipo === "texto" && !campo.requerido && valor === "") continue;
    salida[campo.clave] = campo.tipo === "numero" ? Number(valor) : valor;
  }
  return salida;
}

/** Formulario + tabla genéricos: las nueve secciones cambian solo en la definición. */
function Seccion({
  titulo,
  descripcion,
  campos,
  crear,
  rutaBorrado,
  clavesInvalidar,
  columnas,
  filas,
  vacio,
}: {
  titulo: string;
  descripcion: string;
  campos: Campo[];
  crear: (datos: Fila) => Promise<unknown>;
  rutaBorrado: (fila: Fila) => string;
  clavesInvalidar: readonly (readonly unknown[])[];
  columnas: { etiqueta: string; valor: (fila: Fila) => ReactNode }[];
  filas: Fila[] | undefined;
  vacio: string;
}) {
  const cliente = useQueryClient();
  const [valores, setValores] = useState<Record<string, Valor>>(() =>
    Object.fromEntries(campos.map((campo) => [campo.clave, valorInicial(campo)])),
  );
  const [error, setError] = useState<string | null>(null);

  const invalidar = () => {
    for (const clave of clavesInvalidar) {
      void cliente.invalidateQueries({ queryKey: clave });
    }
  };

  const alta = useMutation({
    mutationFn: (datos: Fila) => crear(datos),
    onSuccess: () => {
      setError(null);
      setValores(Object.fromEntries(campos.map((campo) => [campo.clave, valorInicial(campo)])));
      invalidar();
    },
    onError: (fallo) => setError(fallo instanceof Error ? fallo.message : "No se pudo guardar."),
  });

  const baja = useMutation({
    mutationFn: (ruta: string) => borrar(ruta),
    onSuccess: () => {
      setError(null);
      invalidar();
    },
    onError: (fallo) =>
      setError(
        fallo instanceof Error
          ? `No se pudo borrar: ${fallo.message}`
          : "No se pudo borrar: está en uso.",
      ),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>{titulo}</CardTitle>
        <CardDescription>{descripcion}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <form
          aria-label={`Agregar ${titulo}`}
          className="flex flex-wrap items-end gap-3"
          onSubmit={(evento) => {
            evento.preventDefault();
            alta.mutate(aEnviar(campos, valores));
          }}
        >
          {campos.map((campo) => (
            <label
              key={campo.clave}
              className={cn(
                "flex flex-col gap-1 text-label-xs text-mh-secondary",
                campo.tipo === "texto" ? "min-w-[160px]" : "",
              )}
            >
              {campo.etiqueta}
              {campo.tipo === "opcion" ? (
                <select
                  value={String(valores[campo.clave] ?? "")}
                  onChange={(evento) =>
                    setValores((previos) => ({ ...previos, [campo.clave]: evento.target.value }))
                  }
                  className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-2 text-body-sm text-mh-text"
                >
                  {campo.opciones.length === 0 ? <option value="">Sin opciones</option> : null}
                  {campo.opciones.map((opcion) => (
                    <option key={opcion.valor} value={opcion.valor}>
                      {opcion.etiqueta}
                    </option>
                  ))}
                </select>
              ) : campo.tipo === "bool" ? (
                <input
                  type="checkbox"
                  checked={Boolean(valores[campo.clave])}
                  onChange={(evento) =>
                    setValores((previos) => ({ ...previos, [campo.clave]: evento.target.checked }))
                  }
                  className="size-5 accent-[var(--mh-accent)]"
                />
              ) : (
                <input
                  type={campo.tipo === "numero" ? "number" : campo.tipo === "hora" ? "time" : "text"}
                  value={String(valores[campo.clave] ?? "")}
                  min={campo.tipo === "numero" ? campo.min : undefined}
                  step={campo.tipo === "numero" ? 1 : undefined}
                  onChange={(evento) =>
                    setValores((previos) => ({ ...previos, [campo.clave]: evento.target.value }))
                  }
                  className="min-h-[44px] w-full rounded-sm border border-mh-border-control bg-mh-canvas px-2 text-body-sm text-mh-text"
                />
              )}
            </label>
          ))}
          <Button type="submit" size="sm" disabled={alta.isPending}>
            <Plus aria-hidden="true" />
            {alta.isPending ? "Guardando…" : "Agregar"}
          </Button>
        </form>

        {error ? <Aviso tono="error">{error}</Aviso> : null}

        {filas === undefined ? (
          <Cargando que={titulo.toLowerCase()} />
        ) : filas.length === 0 ? (
          <Vacio titulo={vacio} />
        ) : (
          <div className="mh-scroll-x">
          <table className="w-full min-w-[560px] text-body-sm">
            <caption className="sr-only">{titulo}</caption>
            <thead>
              <tr className="border-b border-mh-border text-left text-mh-muted">
                {columnas.map((columna) => (
                  <th key={columna.etiqueta} scope="col" className="pb-2">
                    {columna.etiqueta}
                  </th>
                ))}
                <th scope="col" className="pb-2 text-right">
                  <span className="sr-only">Acciones</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {filas.map((fila) => (
                <tr
                  key={String(fila.id ?? fila.codigo ?? `${fila.docente_id}-${fila.asignatura_id}`)}
                  className="border-b border-mh-border last:border-0"
                >
                  {columnas.map((columna) => (
                    <td key={columna.etiqueta} className="py-2 text-mh-secondary">
                      {columna.valor(fila)}
                    </td>
                  ))}
                  <td className="py-2 text-right">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => baja.mutate(rutaBorrado(fila))}
                      disabled={baja.isPending}
                      aria-label={`Borrar ${columnas[0]?.valor(fila) ?? ""}`}
                    >
                      <Trash2 aria-hidden="true" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function Configuracion() {
  const grados = useQuery({ queryKey: clavesConsulta.grados, queryFn: listarGrados });
  const bloques = useQuery({ queryKey: clavesConsulta.bloques, queryFn: listarBloques });
  const asignaturas = useQuery({
    queryKey: clavesConsulta.asignaturas,
    queryFn: listarAsignaturas,
  });
  const tipos = useQuery({ queryKey: clavesConsulta.tiposRecurso, queryFn: listarTiposRecurso });
  const cursos = useQuery({ queryKey: clavesConsulta.cursos, queryFn: listarCursos });
  const docentes = useQuery({ queryKey: clavesConsulta.docentes, queryFn: listarDocentes });
  const recursos = useQuery({ queryKey: clavesConsulta.recursos, queryFn: listarRecursos });
  const asignaciones = useQuery({
    queryKey: clavesConsulta.asignaciones,
    queryFn: listarAsignaciones,
  });
  const aptitudes = useQuery({ queryKey: clavesConsulta.aptitudes, queryFn: listarAptitudes });

  const opcionesGrado = (grados.data ?? []).map((grado) => ({
    valor: grado.id,
    etiqueta: `${grado.orden}° · ${grado.nombre}`,
  }));
  const opcionesCurso = (cursos.data ?? []).map((curso) => ({
    valor: curso.id,
    etiqueta: curso.codigo,
  }));
  const opcionesDocente = (docentes.data ?? []).map((docente) => ({
    valor: docente.id,
    etiqueta: `${docente.codigo} · ${docente.nombre}`,
  }));
  const opcionesAsignatura = (asignaturas.data ?? []).map((asignatura) => ({
    valor: asignatura.id,
    etiqueta: asignatura.nombre,
  }));
  const opcionesTipo = (tipos.data ?? []).map((tipo) => ({
    valor: tipo.codigo,
    etiqueta: tipo.codigo.replaceAll("_", " "),
  }));

  const nombreCurso = (id: unknown) =>
    cursos.data?.find((curso) => curso.id === id)?.codigo ?? "—";
  const nombreDocente = (id: unknown) => {
    const docente = docentes.data?.find((item) => item.id === id);
    return docente ? `${docente.codigo} · ${docente.nombre}` : "—";
  };
  const nombreAsignatura = (id: unknown) =>
    asignaturas.data?.find((item) => item.id === id)?.nombre ?? "—";

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Configuración
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          Todo lo que el Excel trae se puede cargar a mano acá. Sirve para un colegio que todavía no
          tiene el archivo armado, o cuando la importación falla.
        </p>
      </div>

      <Aviso tono="info">
        El orden importa: grados → bloques → asignaturas → tipos de recurso → cursos, docentes y
        recursos → asignaciones → aptitudes. Sin aptitudes, el solver no puede repartir una
        asignatura entre dos docentes.
      </Aviso>

      <Seccion
        titulo="Grados"
        descripcion="Los años escolares. Un curso siempre pertenece a uno."
        campos={[
          { tipo: "texto", clave: "nombre", etiqueta: "Nombre", requerido: true },
          { tipo: "numero", clave: "orden", etiqueta: "Orden", defecto: 1, min: 0 },
        ]}
        crear={(datos) => crearGrado(datos as { nombre: string; orden: number })}
        rutaBorrado={(fila) => `/grados/${String(fila.id)}`}
        clavesInvalidar={[clavesConsulta.grados, clavesConsulta.cursos]}
        columnas={[
          { etiqueta: "Orden", valor: (fila) => String(fila.orden) },
          { etiqueta: "Nombre", valor: (fila) => String(fila.nombre) },
        ]}
        filas={grados.data as unknown as Fila[] | undefined}
        vacio="Todavía no hay grados"
      />

      <Seccion
        titulo="Bloques"
        descripcion="Franjas del día. Los recreos y el almuerzo se cargan acá con su tipo: nunca admiten sesiones."
        campos={[
          { tipo: "texto", clave: "codigo", etiqueta: "Código", requerido: true },
          { tipo: "numero", clave: "orden", etiqueta: "Orden", defecto: 1, min: 0 },
          { tipo: "hora", clave: "inicio", etiqueta: "Inicio", defecto: "07:00" },
          { tipo: "hora", clave: "fin", etiqueta: "Fin", defecto: "08:00" },
          {
            tipo: "opcion",
            clave: "tipo",
            etiqueta: "Tipo",
            opciones: [
              { valor: "clase", etiqueta: "Clase" },
              { valor: "descanso", etiqueta: "Recreo" },
              { valor: "almuerzo", etiqueta: "Almuerzo" },
            ],
          },
        ]}
        crear={(datos) =>
          crearBloque(
            datos as { codigo: string; orden: number; inicio: string; fin: string; tipo: string },
          )
        }
        rutaBorrado={(fila) => `/bloques/${String(fila.id)}`}
        clavesInvalidar={[clavesConsulta.bloques]}
        columnas={[
          { etiqueta: "Código", valor: (fila) => String(fila.codigo) },
          { etiqueta: "Tipo", valor: (fila) => String(fila.tipo) },
          {
            etiqueta: "Horario",
            valor: (fila) =>
              `${String(fila.inicio).slice(0, 5)} a ${String(fila.fin).slice(0, 5)}`,
          },
          { etiqueta: "Minutos", valor: (fila) => String(fila.duracion_min) },
        ]}
        filas={bloques.data as unknown as Fila[] | undefined}
        vacio="Todavía no hay bloques"
      />

      <Seccion
        titulo="Asignaturas"
        descripcion="Una materia pesada se penaliza en el solver, nunca se prohíbe (D-006)."
        campos={[
          { tipo: "texto", clave: "nombre", etiqueta: "Nombre", requerido: true },
          { tipo: "texto", clave: "color", etiqueta: "Color", defecto: colorPorDefecto() },
          { tipo: "bool", clave: "es_pesada", etiqueta: "Es pesada" },
        ]}
        crear={(datos) =>
          crearAsignatura(datos as { nombre: string; color: string; es_pesada: boolean })
        }
        rutaBorrado={(fila) => `/asignaturas/${String(fila.id)}`}
        clavesInvalidar={[clavesConsulta.asignaturas, clavesConsulta.asignaciones]}
        columnas={[
          { etiqueta: "Nombre", valor: (fila) => String(fila.nombre) },
          {
            etiqueta: "Pesada",
            valor: (fila) => (fila.es_pesada ? "Sí" : "No"),
          },
        ]}
        filas={asignaturas.data as unknown as Fila[] | undefined}
        vacio="Todavía no hay asignaturas"
      />

      <Seccion
        titulo="Tipos de recurso"
        descripcion="Aulas, laboratorios y canchas. Un recurso siempre tiene un tipo."
        campos={[{ tipo: "texto", clave: "codigo", etiqueta: "Código", requerido: true }]}
        crear={(datos) => crearTipoRecurso(String(datos.codigo))}
        rutaBorrado={(fila) => `/tipos-recurso/${String(fila.codigo)}`}
        clavesInvalidar={[clavesConsulta.tiposRecurso, clavesConsulta.recursos]}
        columnas={[{ etiqueta: "Código", valor: (fila) => String(fila.codigo) }]}
        filas={tipos.data as unknown as Fila[] | undefined}
        vacio="Todavía no hay tipos de recurso"
      />

      <Seccion
        titulo="Cursos"
        descripcion="Cada curso ocupa los 30 bloques de la semana."
        campos={[
          { tipo: "texto", clave: "codigo", etiqueta: "Código", requerido: true },
          { tipo: "texto", clave: "nombre", etiqueta: "Nombre", requerido: true },
          { tipo: "opcion", clave: "grado_id", etiqueta: "Grado", opciones: opcionesGrado },
          { tipo: "numero", clave: "estudiantes", etiqueta: "Estudiantes", defecto: 30, min: 0 },
        ]}
        crear={(datos) =>
          crearCurso(
            datos as { codigo: string; nombre: string; grado_id: string; estudiantes: number },
          )
        }
        rutaBorrado={(fila) => `/cursos/${String(fila.id)}`}
        clavesInvalidar={[clavesConsulta.cursos]}
        columnas={[
          { etiqueta: "Código", valor: (fila) => String(fila.codigo) },
          { etiqueta: "Nombre", valor: (fila) => String(fila.nombre) },
          { etiqueta: "Estudiantes", valor: (fila) => String(fila.estudiantes) },
        ]}
        filas={cursos.data as unknown as Fila[] | undefined}
        vacio="Todavía no hay cursos"
      />

      <Seccion
        titulo="Docentes"
        descripcion="El máximo se cuenta en sesiones (bloques), no en horas."
        campos={[
          { tipo: "texto", clave: "codigo", etiqueta: "Código", requerido: true },
          { tipo: "texto", clave: "nombre", etiqueta: "Nombre", requerido: true },
          {
            tipo: "numero",
            clave: "max_sesiones_semana",
            etiqueta: "Máximo semanal",
            defecto: 24,
            min: 0,
          },
        ]}
        crear={(datos) =>
          crearDocente(datos as { codigo: string; nombre: string; max_sesiones_semana: number })
        }
        rutaBorrado={(fila) => `/docentes/${String(fila.id)}`}
        clavesInvalidar={[clavesConsulta.docentes, clavesConsulta.aptitudes]}
        columnas={[
          { etiqueta: "Código", valor: (fila) => String(fila.codigo) },
          { etiqueta: "Nombre", valor: (fila) => String(fila.nombre) },
          { etiqueta: "Máximo", valor: (fila) => String(fila.max_sesiones_semana) },
        ]}
        filas={docentes.data as unknown as Fila[] | undefined}
        vacio="Todavía no hay docentes"
      />

      <Seccion
        titulo="Recursos"
        descripcion="Un recurso con curso titular es el aula propia de ese curso."
        campos={[
          { tipo: "texto", clave: "codigo", etiqueta: "Código", requerido: true },
          { tipo: "texto", clave: "nombre", etiqueta: "Nombre", requerido: true },
          { tipo: "opcion", clave: "tipo_recurso", etiqueta: "Tipo", opciones: opcionesTipo },
          { tipo: "numero", clave: "capacidad", etiqueta: "Capacidad", defecto: 30, min: 0 },
        ]}
        crear={(datos) =>
          crearRecurso(
            datos as {
              codigo: string;
              nombre: string;
              tipo_recurso: string;
              capacidad: number;
            },
          )
        }
        rutaBorrado={(fila) => `/recursos/${String(fila.id)}`}
        clavesInvalidar={[clavesConsulta.recursos]}
        columnas={[
          { etiqueta: "Código", valor: (fila) => String(fila.codigo) },
          { etiqueta: "Tipo", valor: (fila) => String(fila.tipo_recurso) },
          { etiqueta: "Capacidad", valor: (fila) => String(fila.capacidad) },
        ]}
        filas={recursos.data as unknown as Fila[] | undefined}
        vacio="Todavía no hay recursos"
      />

      <Seccion
        titulo="Carga académica"
        descripcion="Cuántas sesiones semanales de una asignatura necesita un curso, y con quién."
        campos={[
          { tipo: "opcion", clave: "curso_id", etiqueta: "Curso", opciones: opcionesCurso },
          {
            tipo: "opcion",
            clave: "asignatura_id",
            etiqueta: "Asignatura",
            opciones: opcionesAsignatura,
          },
          {
            tipo: "opcion",
            clave: "docente_principal_id",
            etiqueta: "Docente",
            opciones: opcionesDocente,
          },
          { tipo: "numero", clave: "sesiones_semana", etiqueta: "Sesiones", defecto: 4, min: 0 },
          {
            tipo: "opcion",
            clave: "tipo_recurso_requerido",
            etiqueta: "Aula requerida",
            opciones: opcionesTipo,
          },
        ]}
        crear={(datos) =>
          crearAsignacion(
            datos as {
              curso_id: string;
              asignatura_id: string;
              docente_principal_id: string;
              sesiones_semana: number;
              tipo_recurso_requerido: string;
            },
          )
        }
        rutaBorrado={(fila) => `/asignaciones/${String(fila.id)}`}
        clavesInvalidar={[clavesConsulta.asignaciones]}
        columnas={[
          { etiqueta: "Curso", valor: (fila) => nombreCurso(fila.curso_id) },
          { etiqueta: "Asignatura", valor: (fila) => nombreAsignatura(fila.asignatura_id) },
          { etiqueta: "Docente", valor: (fila) => nombreDocente(fila.docente_principal_id) },
          { etiqueta: "Sesiones", valor: (fila) => String(fila.sesiones_semana) },
        ]}
        filas={asignaciones.data as unknown as Fila[] | undefined}
        vacio="Todavía no hay carga académica"
      />

      <Seccion
        titulo="Aptitudes"
        descripcion="Quién puede dictar qué. Es lo que permite repartir una asignatura entre dos docentes."
        campos={[
          {
            tipo: "opcion",
            clave: "docente_id",
            etiqueta: "Docente",
            opciones: opcionesDocente,
          },
          {
            tipo: "opcion",
            clave: "asignatura_id",
            etiqueta: "Asignatura",
            opciones: opcionesAsignatura,
          },
        ]}
        crear={(datos) => crearAptitud(datos as { docente_id: string; asignatura_id: string })}
        rutaBorrado={(fila) => `/aptitudes/${String(fila.docente_id)}/${String(fila.asignatura_id)}`}
        clavesInvalidar={[clavesConsulta.aptitudes]}
        columnas={[
          { etiqueta: "Docente", valor: (fila) => nombreDocente(fila.docente_id) },
          { etiqueta: "Asignatura", valor: (fila) => nombreAsignatura(fila.asignatura_id) },
        ]}
        filas={aptitudes.data as unknown as Fila[] | undefined}
        vacio="Todavía no hay aptitudes"
      />
    </section>
  );
}
