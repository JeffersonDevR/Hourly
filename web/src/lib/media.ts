import { useEffect, useState } from "react";

/**
 * Media query reactiva. Tolera entornos sin `matchMedia` (jsdom en los tests):
 * ahí devuelve `false`, o sea el layout ancho.
 */
export function useMediaQuery(consulta: string): boolean {
  const soportado = () =>
    typeof window !== "undefined" && typeof window.matchMedia === "function";
  const leer = () => (soportado() ? window.matchMedia(consulta).matches : false);

  const [coincide, setCoincide] = useState(leer);

  useEffect(() => {
    if (!soportado()) return;
    const media = window.matchMedia(consulta);
    const alCambiar = (evento: MediaQueryListEvent) => setCoincide(evento.matches);
    setCoincide(media.matches);
    media.addEventListener("change", alCambiar);
    return () => media.removeEventListener("change", alCambiar);
  }, [consulta]);

  return coincide;
}

/** Diseño §5: por debajo de 1024 la cuadrícula muestra un día a la vez. */
export const usaGrillaCompacta = () => useMediaQuery("(max-width: 1023px)");

/** Diseño §5: por debajo de 768 no hay layout, solo un aviso de tamaño. */
export const usaAvisoDeTamano = () => useMediaQuery("(max-width: 767px)");
