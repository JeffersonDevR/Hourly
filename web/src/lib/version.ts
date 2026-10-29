/** La versión que la UI muestra: la de `numero` más alto. */
export function versionMasReciente<T extends { numero: number }>(versiones: T[]): T | undefined {
  return [...versiones].sort((a, b) => b.numero - a.numero)[0];
}
