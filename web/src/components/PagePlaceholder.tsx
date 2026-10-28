import { Construction } from "lucide-react";

type Props = {
  titulo: string;
  descripcion: string;
  fase: string;
};

/** Marcador de posición de una pantalla que se construye en una fase posterior. */
export function PagePlaceholder({ titulo, descripcion, fase }: Props) {
  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-4">
      <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
        {titulo}
      </h1>
      <p className="max-w-[70ch] text-body text-mh-secondary">{descripcion}</p>

      <div
        role="status"
        className="mt-2 flex w-fit items-center gap-3 rounded-sm border border-mh-border bg-mh-surface px-4 py-3 text-body-sm text-mh-muted"
      >
        <Construction aria-hidden="true" className="size-5" />
        <span>Pantalla en construcción ({fase}).</span>
      </div>
    </section>
  );
}
