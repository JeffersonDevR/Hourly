import { useQuery } from "@tanstack/react-query";

import { Cargando, ErrorConsulta, Vacio } from "@/components/estados";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { clavesConsulta, listarAsignaciones, listarCursos } from "@/lib/api";

export function Cursos() {
  const cursos = useQuery({ queryKey: clavesConsulta.cursos, queryFn: listarCursos });
  const asignaciones = useQuery({
    queryKey: clavesConsulta.asignaciones,
    queryFn: listarAsignaciones,
  });

  const fallida = cursos.isError ? cursos : asignaciones.isError ? asignaciones : null;

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Cursos
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          Cada curso ocupa los 30 bloques de la semana. La carga dice cuántas sesiones necesita de
          cada asignatura.
        </p>
      </div>

      {cursos.isPending || asignaciones.isPending ? <Cargando que="los cursos" /> : null}
      {fallida ? <ErrorConsulta error={fallida.error} onReintentar={() => void fallida.refetch()} /> : null}

      <Card>
        <CardHeader>
          <CardTitle>Listado</CardTitle>
          <CardDescription>
            {cursos.data?.length ?? 0} cursos · {asignaciones.data?.length ?? 0} asignaciones de carga
          </CardDescription>
        </CardHeader>
        <CardContent>
          {cursos.data?.length === 0 ? (
            <Vacio titulo="Todavía no hay cursos">
              Importá el Excel de la escuela desde <strong>Importar</strong>.
            </Vacio>
          ) : null}

          {cursos.data && cursos.data.length > 0 ? (
            <table className="w-full text-body-sm">
              <caption className="sr-only">Cursos con estudiantes y asignaturas asignadas</caption>
              <thead>
                <tr className="border-b border-mh-border text-left text-mh-muted">
                  <th scope="col" className="pb-2">Código</th>
                  <th scope="col" className="pb-2">Nombre</th>
                  <th scope="col" className="pb-2 text-right">Estudiantes</th>
                  <th scope="col" className="pb-2 text-right">Asignaturas</th>
                </tr>
              </thead>
              <tbody>
                {cursos.data.map((curso) => (
                  <tr key={curso.id} className="border-b border-mh-border last:border-0">
                    <td className="py-3 text-label text-mh-text">{curso.codigo}</td>
                    <td className="py-3 text-mh-secondary">{curso.nombre}</td>
                    <td className="py-3 text-right tabular-nums text-mh-secondary">
                      {curso.estudiantes}
                    </td>
                    <td className="py-3 text-right tabular-nums text-mh-secondary">
                      {asignaciones.data?.filter((carga) => carga.curso_id === curso.id).length ?? 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
        </CardContent>
      </Card>
    </section>
  );
}
