import {
  AlertTriangle,
  CalendarDays,
  DoorOpen,
  GitBranch,
  GraduationCap,
  LayoutDashboard,
  Scale,
  Settings,
  Share2,
  Upload,
  Users,
  type LucideIcon,
} from "lucide-react";

export type ItemNavegacion = {
  ruta: string;
  etiqueta: string;
  icono: LucideIcon;
};

/**
 * Los **siete destinos** de la barra lateral (`design/stitch/README.md` §3). No crece:
 * el escenario vive en la barra superior y el resto son pantallas secundarias.
 */
export const NAVEGACION: ItemNavegacion[] = [
  { ruta: "/", etiqueta: "Inicio", icono: LayoutDashboard },
  { ruta: "/importar", etiqueta: "Importar", icono: Upload },
  { ruta: "/horario", etiqueta: "Horario", icono: CalendarDays },
  { ruta: "/conflictos", etiqueta: "Conflictos", icono: AlertTriangle },
  { ruta: "/docentes", etiqueta: "Docentes", icono: Users },
  { ruta: "/recursos", etiqueta: "Recursos", icono: DoorOpen },
  { ruta: "/publicacion", etiqueta: "Publicar", icono: Share2 },
];

/**
 * Cursos y Reglas son secundarias en el diseño (se llegan desde Inicio y Conflictos).
 * Se listan acá, más chicas, para que sus rutas no queden huérfanas. Desviación
 * documentada en `design/stitch/README.md`.
 */
export const NAVEGACION_SECUNDARIA: ItemNavegacion[] = [
  { ruta: "/cursos", etiqueta: "Cursos", icono: GraduationCap },
  { ruta: "/reglas", etiqueta: "Reglas", icono: Scale },
  { ruta: "/escenario", etiqueta: "Escenario", icono: GitBranch },
  { ruta: "/configuracion", etiqueta: "Ajustes", icono: Settings },
];
