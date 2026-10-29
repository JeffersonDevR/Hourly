import { useQuery } from "@tanstack/react-query";

import { Cargando, ErrorConsulta, Vacio } from "@/components/estados";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { clavesConsulta, listarCursos, listarRecursos } from "@/lib/api";
import type { Recurso } from "@/types/api";

export function Recursos() {
  const recursos = useQuery({ queryKey: clavesConsulta.recursos, queryFn: listarRecursos });
  const cursos = useQuery({ queryKey: clavesConsulta.cursos, queryFn: listarCursos });

  const fallida = recursos.isError ? recursos : cursos.isError ? cursos : null;
  const nombreCurso = (id: string | null) =>
    id ? (cursos.data?.find((curso) => curso.id === id)?.codigo ?? "—") : null;

  const porTipo = new Map<string, Recurso[]>();
  for (const recurso of recursos.data ?? []) {
    const lista = porTipo.get(recurso.tipo_recurso) ?? [];
    lista.push(recurso);
    porTipo.set(recurso.tipo_recurso, lista);
  }

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Recursos
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          Aulas, laboratorios y canchas. Un recurso con curso titular es el aula propia de ese curso;
          el resto se comparte.
        </p>
      </div>

      {recursos.isPending || cursos.isPending ? <Cargando que="los recursos" /> : null}
      {fallida ? <ErrorConsulta error={fallida.error} onReintentar={() => void fallida.refetch()} /> : null}

      {recursos.data?.length === 0 ? (
        <Vacio titulo="Todavía no hay recursos">
          Importá el Excel de la escuela desde <strong>Importar</strong>.
        </Vacio>
      ) : null}

      {[...porTipo.entries()].map(([tipo, lista]) => (
        <Card key={tipo}>
          <CardHeader>
            <CardTitle>{tipo.replaceAll("_", " ")}</CardTitle>
            <CardDescription>{lista.length} recursos de este tipo</CardDescription>
          </CardHeader>
          <CardContent>
            <table className="w-full text-body-sm">
              <caption className="sr-only">Recursos de tipo {tipo}</caption>
              <thead>
                <tr className="border-b border-mh-border text-left text-mh-muted">
                  <th scope="col" className="pb-2">Código</th>
                  <th scope="col" className="pb-2">Nombre</th>
                  <th scope="col" className="pb-2 text-right">Capacidad</th>
                  <th scope="col" className="pb-2 text-right">Aula titular</th>
                </tr>
              </thead>
              <tbody>
                {lista.map((recurso) => (
                  <tr key={recurso.id} className="border-b border-mh-border last:border-0">
                    <td className="py-3 text-label text-mh-text">{recurso.codigo}</td>
                    <td className="py-3 text-mh-secondary">{recurso.nombre}</td>
                    <td className="py-3 text-right tabular-nums text-mh-secondary">
                      {recurso.capacidad}
                    </td>
                    <td className="py-3 text-right text-mh-muted">
                      {nombreCurso(recurso.curso_titular_id) ?? "Compartido"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      ))}
    </section>
  );
}
