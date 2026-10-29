import type {
  Aptitud,
  Asignacion,
  Asignatura,
  Bloque,
  Conflicto,
  Curso,
  Docente,
  Estado,
  EstadoVersion,
  Escenario,
  Grado,
  PreviewImportacion,
  Recurso,
  Sesion,
  TipoRecurso,
  Version,
} from "@/types/api";

const BASE = "/api";

/** Error de la API con el `{codigo, mensaje}` que devuelve el backend. */
export class ErrorApi extends Error {
  constructor(
    readonly estado: number,
    readonly codigo: string,
    mensaje: string,
  ) {
    super(mensaje);
    this.name = "ErrorApi";
  }
}

async function pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
  const respuesta = await fetch(`${BASE}${ruta}`, {
    headers: { Accept: "application/json", ...init?.headers },
    ...init,
  });

  if (!respuesta.ok) {
    let codigo = "ERROR";
    let mensaje = `La API respondió ${respuesta.status}.`;
    try {
      const cuerpo = (await respuesta.json()) as { codigo?: string; mensaje?: string };
      codigo = cuerpo.codigo ?? codigo;
      mensaje = cuerpo.mensaje ?? mensaje;
    } catch {
      // Sin cuerpo JSON: el mensaje por defecto ya explica el status.
    }
    throw new ErrorApi(respuesta.status, codigo, mensaje);
  }

  if (respuesta.status === 204) {
    return undefined as T;
  }
  return (await respuesta.json()) as T;
}

function json(cuerpo: unknown): RequestInit {
  return { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) };
}

// --- estado y catálogos -------------------------------------------------------------

export const obtenerEstado = () => pedir<Estado>("/estado");
export const listarCursos = () => pedir<Curso[]>("/cursos");
export const listarDocentes = () => pedir<Docente[]>("/docentes");
export const listarRecursos = () => pedir<Recurso[]>("/recursos");
export const listarBloques = () => pedir<Bloque[]>("/bloques");
export const listarAsignaturas = () => pedir<Asignatura[]>("/asignaturas");
export const listarAsignaciones = () => pedir<Asignacion[]>("/asignaciones");
export const listarEscenarios = () => pedir<Escenario[]>("/escenarios");

export const crearCurso = (datos: {
  codigo: string;
  nombre: string;
  grado_id: string;
  estudiantes: number;
}) => pedir<Curso>("/cursos", json(datos));

export const crearDocente = (datos: {
  codigo: string;
  nombre: string;
  max_sesiones_semana: number;
}) => pedir<Docente>("/docentes", json(datos));

export const listarGrados = () => pedir<Grado[]>("/grados");
export const listarTiposRecurso = () => pedir<TipoRecurso[]>("/tipos-recurso");
export const listarAptitudes = () => pedir<Aptitud[]>("/aptitudes");

export const crearGrado = (datos: { nombre: string; orden: number }) =>
  pedir<Grado>("/grados", json(datos));

export const crearBloque = (datos: {
  codigo: string;
  orden: number;
  inicio: string;
  fin: string;
  tipo: string;
}) => pedir<Bloque>("/bloques", json(datos));

export const crearAsignatura = (datos: {
  nombre: string;
  color: string;
  es_pesada: boolean;
}) => pedir<Asignatura>("/asignaturas", json(datos));

export const crearAsignacion = (datos: {
  curso_id: string;
  asignatura_id: string;
  docente_principal_id: string;
  sesiones_semana: number;
  tipo_recurso_requerido: string;
}) => pedir<Asignacion>("/asignaciones", json(datos));

export const crearTipoRecurso = (codigo: string) =>
  pedir<TipoRecurso>("/tipos-recurso", json({ codigo }));

export const crearAptitud = (datos: { docente_id: string; asignatura_id: string }) =>
  pedir<Aptitud>("/aptitudes", json(datos));

/** `DELETE` genérico: la ruta la arma quien llama. La API responde 204. */
export const borrar = (ruta: string) => pedir<void>(ruta, { method: "DELETE" });

export const crearRecurso = (datos: {
  codigo: string;
  nombre: string;
  tipo_recurso: string;
  capacidad: number;
}) => pedir<Recurso>("/recursos", json(datos));

// --- importación --------------------------------------------------------------------

export async function subirImportacion(archivo: File): Promise<PreviewImportacion> {
  const cuerpo = new FormData();
  cuerpo.append("archivo", archivo);
  return pedir<PreviewImportacion>("/importaciones", { method: "POST", body: cuerpo });
}

export const corregirFilas = (
  id: string,
  correcciones: { hoja: string; fila: number; columna: string; valor: string | number }[],
) => pedir<PreviewImportacion>(`/importaciones/${id}/filas`, { ...json({ correcciones }), method: "PATCH" });

export const confirmarImportacion = (id: string) =>
  pedir<PreviewImportacion & { resultado: Record<string, number> }>(
    `/importaciones/${id}/confirmar`,
    { method: "POST" },
  );

// --- reglas en lenguaje natural -----------------------------------------------------

export type ReglaInterpretada = {
  docente_codigo: string;
  docente_nombre: string;
  dias: number[];
  bloque_codigo: string | null;
  bloquea: boolean;
  motivo: string | null;
};

export type RespuestaInterpretar = {
  regla: ReglaInterpretada | null;
  origen: "determinista" | "ia" | "manual";
  mensaje: string | null;
};

export const interpretarRegla = (texto: string) =>
  pedir<RespuestaInterpretar>("/reglas/interpretar", json({ texto }));

export const confirmarRegla = (datos: {
  docente_codigo: string;
  dias: number[];
  bloque_codigo?: string | null;
  bloquea: boolean;
  motivo?: string | null;
}) => pedir<{ creados: number; eliminados: number; bloques: string[] }>("/reglas/confirmar", json(datos));

// --- propuestas ---------------------------------------------------------------------

export type Propuesta = {
  id: string;
  origen: "solver" | "ia";
  titulo: string;
  explicacion: string;
  impacto: string | null;
  estado: string;
  cambios: { id: string; tipo: string; datos: Record<string, unknown> }[];
};

export type RespuestaPropuestas = {
  propuestas: Propuesta[];
  alerta: { codigo: string; gravedad: string; mensaje: string }[];
};

export const proponerSolucion = (conflictoId: string) =>
  pedir<RespuestaPropuestas>(`/conflictos/${conflictoId}/propuestas`, { method: "POST" });

export const aceptarPropuesta = (propuestaId: string) =>
  pedir<{ id: string; estado: string }>(`/propuestas/${propuestaId}/aceptar`, { method: "POST" });

export const rechazarPropuesta = (propuestaId: string) =>
  pedir<{ id: string; estado: string }>(`/propuestas/${propuestaId}/rechazar`, { method: "POST" });

// --- horarios -----------------------------------------------------------------------

export const listarVersiones = () => pedir<Version[]>("/horarios");

export const crearVersion = (
  datos: { nota?: string; copiar_de?: string } = {},
) => pedir<Version>("/horarios", json(datos));

export const vistaHorario = (versionId: string) =>
  pedir<{ por: string; sesiones: Sesion[] }>(`/horarios/${versionId}/vista`);

export const listarConflictos = (versionId: string) =>
  pedir<{ conflictos: Conflicto[] }>(`/horarios/${versionId}/conflictos`);

export const validarVersion = (versionId: string) =>
  pedir<{ conflictos: Conflicto[] }>(`/horarios/${versionId}/validar`, json({}));

export const generarHorario = (
  versionId: string,
  opciones: { modo_docente: "principal" | "habilitados"; solo_curso_id?: string | null },
) =>
  pedir<{
    estado: string;
    sesiones: number;
    objetivo: number | null;
    diagnostico: { codigo: string; gravedad: string; mensaje: string }[];
    conflictos: Conflicto[];
  }>(
    `/horarios/${versionId}/generar`,
    json({
      modo_docente: opciones.modo_docente,
      solo_curso_id: opciones.solo_curso_id ?? null,
    }),
  );

export type CeldaArrastre = {
  dia: number;
  bloque_id: string;
  estado: "valida" | "advertencia" | "bloqueada";
  motivo: string | null;
};

export const arrastre = (versionId: string, asignacionId: string) =>
  pedir<{ celdas: CeldaArrastre[] }>(
    `/horarios/${versionId}/arrastre?asignacion_id=${asignacionId}`,
  );

export const colocarSesion = (
  versionId: string,
  datos: {
    asignacion_carga_id: string;
    dia: number;
    bloque_id: string;
    docente_id?: string;
    recurso_id?: string;
  },
) => pedir<Sesion>(`/horarios/${versionId}/sesiones`, json(datos));

export const moverSesion = (
  versionId: string,
  sesionId: string,
  cambios: { dia?: number; bloque_id?: string; fijada?: boolean },
) =>
  pedir<Sesion>(`/horarios/${versionId}/sesiones/${sesionId}`, {
    ...json(cambios),
    method: "PATCH",
  });

export const quitarSesion = (versionId: string, sesionId: string) =>
  pedir<void>(`/horarios/${versionId}/sesiones/${sesionId}`, { method: "DELETE" });

export const deshacerVersion = (versionId: string) =>
  pedir<Record<string, unknown>>(`/horarios/${versionId}/deshacer`, { method: "POST" });

export const rehacerVersion = (versionId: string) =>
  pedir<Record<string, unknown>>(`/horarios/${versionId}/rehacer`, { method: "POST" });

export const publicarVersion = (versionId: string) =>
  pedir<Version>(`/horarios/${versionId}/publicar`, { method: "POST" });

export const urlExportar = (versionId: string, por: string, formato: "xlsx" | "pdf" = "xlsx") =>
  `${BASE}/horarios/${versionId}/exportar?formato=${formato}&por=${por}`;

export type ProspectoEscenario = {
  escenario: { id: string; nombre: string };
  aplicado: boolean;
  sesiones_afectadas: number;
  resultado: {
    estado: string;
    sesiones: number;
    objetivo: number | null;
    diagnostico: { codigo: string; gravedad: string; mensaje: string }[];
  };
  conflictos: { codigo: string; gravedad: string; mensaje: string; sesion_ids?: string[] }[];
};

export const probarEscenario = (
  versionId: string,
  datos: { escenario_id: string; aplicar: boolean },
) => pedir<ProspectoEscenario>(`/horarios/${versionId}/escenario`, json(datos));

// --- claves de TanStack Query -------------------------------------------------------

export const clavesConsulta = {
  estado: ["estado"] as const,
  cursos: ["cursos"] as const,
  docentes: ["docentes"] as const,
  recursos: ["recursos"] as const,
  bloques: ["bloques"] as const,
  asignaturas: ["asignaturas"] as const,
  asignaciones: ["asignaciones"] as const,
  escenarios: ["escenarios"] as const,
  grados: ["grados"] as const,
  tiposRecurso: ["tipos-recurso"] as const,
  aptitudes: ["aptitudes"] as const,
  versiones: ["versiones"] as const,
  versionActiva: ["versiones", "activa"] as const,
  conflictos: (versionId: string) => ["conflictos", versionId] as const,
  sesiones: (versionId: string) => ["sesiones", versionId] as const,
  arrastre: (versionId: string, asignacionId: string) =>
    ["arrastre", versionId, asignacionId] as const,
};

export type { EstadoVersion };
