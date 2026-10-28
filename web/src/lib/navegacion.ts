import {
  AlertTriangle,
  CalendarDays,
  DoorOpen,
  GraduationCap,
  LayoutDashboard,
  Scale,
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

/** Las 9 rutas de ARCHITECTURE.md, en el orden del flujo de trabajo. */
export const NAVEGACION: ItemNavegacion[] = [
  { ruta: "/", etiqueta: "Inicio", icono: LayoutDashboard },
  { ruta: "/importar", etiqueta: "Importar", icono: Upload },
  { ruta: "/cursos", etiqueta: "Cursos", icono: GraduationCap },
  { ruta: "/docentes", etiqueta: "Docentes", icono: Users },
  { ruta: "/recursos", etiqueta: "Recursos", icono: DoorOpen },
  { ruta: "/reglas", etiqueta: "Reglas", icono: Scale },
  { ruta: "/horario", etiqueta: "Horario", icono: CalendarDays },
  { ruta: "/conflictos", etiqueta: "Conflictos", icono: AlertTriangle },
  { ruta: "/publicacion", etiqueta: "Publicación", icono: Share2 },
];
