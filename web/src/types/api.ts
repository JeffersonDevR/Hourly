/** Contratos de la API (`docs/openapi.json`). Tipos escritos a mano hasta que la UI los consuma todos. */

export type Estado = {
  ok: boolean;
  ai_disponible: boolean;
};

export type Curso = {
  id: string;
  codigo: string;
  nombre: string;
  grado_id: string;
  estudiantes: number;
};

export type Docente = {
  id: string;
  codigo: string;
  nombre: string;
  max_sesiones_semana: number;
  activo: boolean;
};

export type Recurso = {
  id: string;
  codigo: string;
  nombre: string;
  tipo_recurso: string;
  capacidad: number;
  curso_titular_id: string | null;
};

export type Bloque = {
  id: string;
  codigo: string;
  orden: number;
  inicio: string;
  fin: string;
  duracion_min: number;
  tipo: string;
};

export type Asignatura = {
  id: string;
  nombre: string;
  color: string;
  es_pesada: boolean;
};

export type Grado = {
  id: string;
  nombre: string;
  orden: number;
};

export type TipoRecurso = {
  codigo: string;
};

export type Aptitud = {
  docente_id: string;
  asignatura_id: string;
};

export type Asignacion = {
  id: string;
  curso_id: string;
  asignatura_id: string;
  docente_principal_id: string;
  sesiones_semana: number;
  tipo_recurso_requerido: string;
};

export type EstadoVersion = "borrador" | "publicado" | "archivado";

export type Version = {
  id: string;
  numero: number;
  estado: EstadoVersion;
  escenario_id: string | null;
  nota: string | null;
  publicado_at: string | null;
};

export type Sesion = {
  id: string;
  horario_version_id: string;
  asignacion_carga_id: string;
  curso_id: string;
  docente_id: string;
  dia: number;
  bloque_id: string;
  recurso_id: string | null;
  fijada: boolean;
};

export type Escenario = {
  id: string;
  nombre: string;
  descripcion: string | null;
};

export type Gravedad = "error" | "advertencia";

export type Conflicto = {
  id: string;
  codigo: string;
  gravedad: Gravedad;
  estado: string;
  mensaje: string;
  sesion_ids: string[];
};

export type Hallazgo = {
  codigo: string;
  severidad: Gravedad;
  mensaje: string;
  hoja: string | null;
  fila: number | null;
  columna: string | null;
  bloqueante: boolean;
};

export type Diagnostico = {
  codigo: string;
  gravedad: Gravedad;
  mensaje: string;
  docente_codigo: string | null;
};

export type PreviewImportacion = {
  id: string;
  estado: string;
  archivo_nombre: string;
  conteos: Record<string, number>;
  hallazgos: Hallazgo[];
  diagnosticos: Diagnostico[];
  errores: number;
  advertencias: number;
  codigos: string[];
  confirmable: boolean;
  escenario: { nombre: string; descripcion: string | null; cambios: number } | null;
};
