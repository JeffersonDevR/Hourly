import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Download, FileSpreadsheet, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";

import { Aviso, ErrorConsulta, Vacio } from "@/components/estados";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  clavesConsulta,
  confirmarImportacion,
  corregirFilas,
  subirImportacion,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Hallazgo, PreviewImportacion } from "@/types/api";

const PASOS = ["Subir", "Mapear", "Revisar", "Confirmar"] as const;

function Pasos({ actual }: { actual: number }) {
  return (
    <ol className="flex flex-wrap items-center gap-2" aria-label="Pasos de la importación">
      {PASOS.map((paso, indice) => {
        const numero = indice + 1;
        const hecho = numero < actual;
        const activo = numero === actual;
        return (
          <li key={paso} className="flex items-center gap-2">
            <span
              aria-current={activo ? "step" : undefined}
              className={cn(
                "flex min-h-[36px] items-center gap-2 rounded-full border px-3 text-label-xs",
                activo && "border-mh-text text-mh-text",
                hecho && "border-mh-border text-mh-success",
                !activo && !hecho && "border-mh-border text-mh-muted",
              )}
            >
              {hecho ? <CheckCircle2 aria-hidden="true" className="size-4" /> : null}
              {numero}. {paso}
              <span className="sr-only">{activo ? " (paso actual)" : hecho ? " (completo)" : ""}</span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function CorreccionFila({
  preview,
  hallazgo,
  onCorregido,
}: {
  preview: PreviewImportacion;
  hallazgo: Hallazgo;
  onCorregido: (nuevo: PreviewImportacion) => void;
}) {
  const [valor, setValor] = useState("");
  const correccion = useMutation({
    mutationFn: () =>
      corregirFilas(preview.id, [
        {
          hoja: hallazgo.hoja ?? "",
          fila: hallazgo.fila ?? 0,
          columna: hallazgo.columna ?? "",
          valor,
        },
      ]),
    onSuccess: onCorregido,
  });

  return (
    <form
      className="mt-2 flex flex-wrap items-center gap-2"
      onSubmit={(evento) => {
        evento.preventDefault();
        correccion.mutate();
      }}
    >
      <label className="text-label-xs text-mh-muted" htmlFor={`corregir-${hallazgo.fila}-${hallazgo.columna}`}>
        Valor correcto
      </label>
      <input
        id={`corregir-${hallazgo.fila}-${hallazgo.columna}`}
        value={valor}
        onChange={(evento) => setValor(evento.target.value)}
        className="min-h-[44px] w-40 rounded-sm border border-mh-border-control bg-mh-canvas px-3 text-body-sm text-mh-text"
      />
      <Button type="submit" size="sm" variant="outline" disabled={!valor || correccion.isPending}>
        {correccion.isPending ? "Corrigiendo…" : "Corregir"}
      </Button>
      {correccion.isError ? <ErrorConsulta error={correccion.error} /> : null}
    </form>
  );
}

export function Importar() {
  const entrada = useRef<HTMLInputElement>(null);
  const [paso, setPaso] = useState(1);
  const [preview, setPreview] = useState<PreviewImportacion | null>(null);
  const cliente = useQueryClient();

  const subida = useMutation({
    mutationFn: subirImportacion,
    onSuccess: (datos) => {
      setPreview(datos);
      setPaso(2);
    },
  });

  const confirmacion = useMutation({
    mutationFn: () => confirmarImportacion(preview!.id),
    onSuccess: () => {
      setPaso(4);
      // El catálogo cambió: Inicio, Cursos y Docentes tienen que releer.
      void cliente.invalidateQueries({ queryKey: clavesConsulta.cursos });
      void cliente.invalidateQueries({ queryKey: clavesConsulta.docentes });
      void cliente.invalidateQueries({ queryKey: clavesConsulta.recursos });
      void cliente.invalidateQueries({ queryKey: clavesConsulta.asignaciones });
    },
  });

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Importar
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          Subí el Excel de la escuela, revisá lo que se detectó, corregí lo que haga falta y
          confirmá. Reimportar el mismo archivo no duplica nada.
        </p>
      </div>

      <Pasos actual={paso} />

      {paso === 1 ? (
        <Card>
          <CardHeader>
            <CardTitle>1. Subir el archivo</CardTitle>
            <CardDescription>Formato .xlsx con las 9 hojas del modelo.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <form
              className="flex flex-wrap items-center gap-3"
              onSubmit={(evento) => {
                evento.preventDefault();
                const archivo = entrada.current?.files?.[0];
                if (archivo) subida.mutate(archivo);
              }}
            >
              <label className="sr-only" htmlFor="archivo">
                Archivo Excel
              </label>
              <input
                id="archivo"
                ref={entrada}
                type="file"
                accept=".xlsx"
                className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-3 py-2 text-body-sm text-mh-secondary file:mr-3 file:rounded-sm file:border-0 file:bg-mh-raised file:px-3 file:py-2 file:text-mh-text"
              />
              <Button type="submit" disabled={subida.isPending}>
                <Upload aria-hidden="true" />
                {subida.isPending ? "Leyendo…" : "Subir"}
              </Button>
              <a
                href="/api/importaciones/plantilla"
                className="inline-flex min-h-[44px] items-center gap-2 rounded-sm border border-mh-border-control px-4 text-label text-mh-text hover:bg-mh-raised"
              >
                <Download aria-hidden="true" className="size-4" />
                Descargar plantilla
              </a>
            </form>
            {subida.isError ? <ErrorConsulta error={subida.error} /> : null}
          </CardContent>
        </Card>
      ) : null}

      {paso === 2 && preview ? (
        <Card>
          <CardHeader>
            <CardTitle>2. Mapear</CardTitle>
            <CardDescription>
              {preview.archivo_nombre}: los encabezados se reconocen solos, esto es lo que se
              detectó.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <table className="w-full text-body-sm">
              <caption className="sr-only">Filas detectadas por entidad</caption>
              <thead>
                <tr className="text-left text-mh-muted">
                  <th scope="col" className="pb-2">Entidad</th>
                  <th scope="col" className="pb-2 text-right">Filas</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(preview.conteos).map(([entidad, filas]) => (
                  <tr key={entidad} className="border-t border-mh-border">
                    <td className="py-2 text-mh-text">{entidad.replaceAll("_", " ")}</td>
                    <td className="py-2 text-right tabular-nums text-mh-secondary">{filas}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {preview.escenario ? (
              <Aviso tono="info">
                Escenario detectado: <strong>{preview.escenario.nombre}</strong> con{" "}
                {preview.escenario.cambios} cambios. No altera el horario base.
              </Aviso>
            ) : null}

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setPaso(1)}>
                Atrás
              </Button>
              <Button onClick={() => setPaso(3)}>Continuar</Button>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {paso === 3 && preview ? (
        <Card>
          <CardHeader>
            <CardTitle>3. Revisar</CardTitle>
            <CardDescription>
              {preview.errores} errores y {preview.advertencias} advertencias. Los errores bloquean
              su fila; las advertencias no bloquean la importación.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {preview.hallazgos.length === 0 ? (
              <Vacio titulo="No hay nada que corregir" />
            ) : (
              <ul className="flex flex-col gap-3">
                {preview.hallazgos.map((hallazgo, indice) => (
                  <li
                    key={`${hallazgo.codigo}-${hallazgo.hoja}-${hallazgo.fila}-${hallazgo.columna}-${indice}`}
                    className="rounded-cell border border-mh-border px-4 py-3"
                  >
                    <p className="flex flex-wrap items-center gap-2 text-label text-mh-text">
                      {hallazgo.severidad === "error" ? (
                        <AlertTriangle aria-hidden="true" className="size-4 text-mh-danger" />
                      ) : (
                        <AlertTriangle aria-hidden="true" className="size-4 text-mh-warning" />
                      )}
                      <span className="text-mh-secondary">
                        {hallazgo.severidad === "error" ? "Error" : "Advertencia"}
                      </span>
                      <code className="rounded-sm bg-mh-raised px-1.5 py-0.5 text-label-xs text-mh-muted">
                        {hallazgo.codigo}
                      </code>
                      {hallazgo.hoja ? (
                        <span className="text-label-xs text-mh-muted">
                          {hallazgo.hoja}
                          {hallazgo.fila ? ` · fila ${hallazgo.fila}` : ""}
                          {hallazgo.columna ? ` · ${hallazgo.columna}` : ""}
                        </span>
                      ) : null}
                    </p>
                    <p className="mt-1 text-body-sm text-mh-secondary">{hallazgo.mensaje}</p>
                    {hallazgo.hoja && hallazgo.fila && hallazgo.columna ? (
                      <CorreccionFila
                        preview={preview}
                        hallazgo={hallazgo}
                        onCorregido={(nuevo) => {
                          setPreview(nuevo);
                          void cliente.invalidateQueries({ queryKey: clavesConsulta.estado });
                        }}
                      />
                    ) : null}
                  </li>
                ))}
              </ul>
            )}

            <div className="flex gap-2">
              <Button variant="outline" onClick={() => setPaso(2)}>
                Atrás
              </Button>
              <Button
                onClick={() => confirmacion.mutate()}
                disabled={!preview.confirmable || confirmacion.isPending}
              >
                <FileSpreadsheet aria-hidden="true" />
                {confirmacion.isPending ? "Confirmando…" : "Confirmar importación"}
              </Button>
            </div>
            {!preview.confirmable ? (
              <Aviso tono="error">
                Ninguna fila quedó válida: corregí las celdas marcadas antes de confirmar.
              </Aviso>
            ) : null}
            {confirmacion.isError ? <ErrorConsulta error={confirmacion.error} /> : null}
          </CardContent>
        </Card>
      ) : null}

      {paso === 4 ? (
        <Card>
          <CardHeader>
            <CardTitle>4. Listo</CardTitle>
            <CardDescription>El catálogo quedó escrito y sin duplicados.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Aviso tono="ok">Importación confirmada.</Aviso>
            <div className="flex flex-wrap gap-2">
              <Button asChild>
                <Link to="/">Ir a Inicio</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link to="/docentes">Revisar docentes</Link>
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  setPreview(null);
                  setPaso(1);
                  confirmacion.reset();
                  subida.reset();
                }}
              >
                Subir otro archivo
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </section>
  );
}
