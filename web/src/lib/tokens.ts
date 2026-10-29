/**
 * Lee un token del sistema de diseño en tiempo de ejecución.
 *
 * Para valores que viajan como dato (el color de una asignatura se guarda como hex en la
 * base), así no queda un literal de color suelto en un componente (G48).
 */
export function leerToken(nombre: string): string {
  if (typeof window === "undefined" || typeof getComputedStyle !== "function") return "";
  return getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
}
