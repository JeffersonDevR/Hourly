/**
 * Marca "Hourly", concepto C: la H geométrica con travesaño lila y bloque crema.
 *
 * Geometría copiada de `design/stitch/logo-opcion-c.svg` (la fuente correcta: las
 * aproximaciones con `<span>` no son el logo). Las verticales usan `currentColor` para
 * poder invertir la marca sobre lila.
 */
export function Marca({
  alto = 32,
  etiqueta = true,
}: {
  alto?: number;
  etiqueta?: boolean;
}) {
  const ancho = Math.round((alto * 30) / 36);

  return (
    <svg
      width={ancho}
      height={alto}
      viewBox="4 6 30 36"
      fill="none"
      role={etiqueta ? "img" : undefined}
      aria-label={etiqueta ? "Hourly" : undefined}
      aria-hidden={etiqueta ? undefined : true}
    >
      <rect x="4" y="6" width="9" height="36" rx="4.5" fill="currentColor" />
      <rect x="25" y="6" width="9" height="24" rx="4.5" fill="currentColor" />
      <rect x="11" y="20" width="16" height="8" rx="4" fill="var(--mh-accent)" />
      <rect x="25" y="34" width="9" height="8" rx="4" fill="var(--mh-cream)" />
    </svg>
  );
}
