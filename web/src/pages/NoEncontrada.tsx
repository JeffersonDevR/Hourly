import { PagePlaceholder } from "@/components/PagePlaceholder";

export function NoEncontrada() {
  return (
    <PagePlaceholder
      titulo="Pantalla no encontrada"
      descripcion="La dirección que abriste no corresponde a ninguna pantalla de Houry."
      fase="navegación"
    />
  );
}
