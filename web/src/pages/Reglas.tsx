import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, Scale, Sparkles } from "lucide-react";
import { useState } from "react";

import { Aviso, Cargando, ErrorConsulta } from "@/components/estados";
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
  confirmarRegla,
  interpretarRegla,
  listarBloques,
  listarDocentes,
  type ReglaInterpretada,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"] as const;

const ORIGEN: Record<string, string> = {
  determinista: "Interpretada por reglas",
  ia: "Interpretada por el asistente",
  manual: "Elegida a mano",
};

const VACIA: ReglaInterpretada = {
  docente_codigo: "",
  docente_nombre: "",
  dias: [],
  bloque_codigo: null,
  bloquea: true,
  motivo: null,
};

export function Reglas() {
  const cliente = useQueryClient();
  const [texto, setTexto] = useState("");
  const [regla, setRegla] = useState<ReglaInterpretada | null>(null);
  const [origen, setOrigen] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [resultado, setResultado] = useState<string | null>(null);

  const docentes = useQuery({ queryKey: clavesConsulta.docentes, queryFn: listarDocentes });
  const bloques = useQuery({
    queryKey: clavesConsulta.bloques,
    queryFn: listarBloques,
    select: (lista) => lista.filter((bloque) => bloque.tipo === "clase"),
  });

  const interpretar = useMutation({
    mutationFn: () => interpretarRegla(texto),
    onSuccess: (datos) => {
      setOrigen(datos.origen);
      setMensaje(datos.mensaje);
      setResultado(null);
      // Sin regla interpretada se abre la tarjeta vacía para elegir a mano (8a).
      setRegla(datos.regla ?? { ...VACIA, docente_codigo: docentes.data?.[0]?.codigo ?? "" });
    },
    onError: () => setResultado("No se pudo interpretar la frase. Probá de nuevo."),
  });

  const confirmar = useMutation({
    mutationFn: () =>
      confirmarRegla({
        docente_codigo: regla!.docente_codigo,
        dias: regla!.dias,
        bloque_codigo: regla!.bloque_codigo,
        bloquea: regla!.bloquea,
        motivo: regla!.motivo ?? texto,
      }),
    onSuccess: (datos) => {
      setResultado(
        datos.creados > 0
          ? `Regla guardada: ${datos.creados} franja(s) bloqueada(s).`
          : datos.eliminados > 0
            ? `Regla guardada: ${datos.eliminados} franja(s) liberada(s).`
            : "La regla ya estaba aplicada: no hubo cambios.",
      );
      void cliente.invalidateQueries({ queryKey: clavesConsulta.docentes });
      void cliente.invalidateQueries({ queryKey: clavesConsulta.versiones });
    },
    onError: () => setResultado("No se pudo guardar la regla."),
  });

  const actualizar = (cambios: Partial<ReglaInterpretada>) =>
    setRegla((previa) => (previa ? { ...previa, ...cambios } : previa));

  const alternarDia = (dia: number) => {
    if (!regla) return;
    const dias = regla.dias.includes(dia)
      ? regla.dias.filter((actual) => actual !== dia)
      : [...regla.dias, dia].sort();
    actualizar({ dias });
  };

  return (
    <section aria-labelledby="titulo-pantalla" className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id="titulo-pantalla" className="text-h1 text-mh-text">
          Reglas
        </h1>
        <p className="max-w-[70ch] text-body text-mh-secondary">
          Escribí la restricción como se la contarías a un coordinador. La regla vuelve editable y
          no se guarda hasta que la confirmes.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>¿Qué regla querés agregar?</CardTitle>
          <CardDescription>Escribila como se la contarías a un coordinador.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <ul className="flex flex-col gap-1 text-body-sm text-mh-muted">
            <li>“D1 no puede los martes”</li>
            <li>“D3 libre el viernes B6”</li>
            <li>“D2 no disponible lunes y miércoles”</li>
          </ul>
          <label className="sr-only" htmlFor="texto-regla">
            Regla en lenguaje natural
          </label>
          <textarea
            id="texto-regla"
            value={texto}
            onChange={(evento) => setTexto(evento.target.value)}
            rows={3}
            className="w-full rounded-sm border border-mh-border-control bg-mh-canvas px-3 py-2 text-body text-mh-text"
            placeholder="D2 no puede los martes"
          />
          <div className="flex items-center gap-3">
            <Button onClick={() => interpretar.mutate()} disabled={texto.trim().length < 3 || interpretar.isPending}>
              <Scale aria-hidden="true" />
              {interpretar.isPending ? "Interpretando…" : "Interpretar"}
            </Button>
            <span aria-live="polite" className="text-label-xs text-mh-muted">
              {interpretar.isPending ? "Consultando el asistente…" : ""}
            </span>
          </div>
          {interpretar.isError ? <ErrorConsulta error={interpretar.error} /> : null}
        </CardContent>
      </Card>

      {docentes.isLoading || bloques.isLoading ? <Cargando que="el catálogo" /> : null}

      {regla ? (
        <Card>
          <CardHeader>
            <CardTitle>Regla interpretada</CardTitle>
            <CardDescription className="flex items-center gap-2">
              <Sparkles aria-hidden="true" className="size-4" />
              {ORIGEN[origen ?? "manual"] ?? "Elegida a mano"}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {mensaje ? <Aviso tono="advertencia">{mensaje}</Aviso> : null}

            <div className="grid gap-3 md:grid-cols-2">
              <label className="flex flex-col gap-1 text-label-xs text-mh-secondary">
                Docente
                <select
                  value={regla.docente_codigo}
                  onChange={(evento) => actualizar({ docente_codigo: evento.target.value })}
                  className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-3 text-body-sm text-mh-text"
                >
                  <option value="">Elegí un docente…</option>
                  {(docentes.data ?? []).map((docente) => (
                    <option key={docente.id} value={docente.codigo}>
                      {docente.codigo} · {docente.nombre}
                    </option>
                  ))}
                </select>
              </label>

              <label className="flex flex-col gap-1 text-label-xs text-mh-secondary">
                Bloque
                <select
                  value={regla.bloque_codigo ?? ""}
                  onChange={(evento) => actualizar({ bloque_codigo: evento.target.value || null })}
                  className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-3 text-body-sm text-mh-text"
                >
                  <option value="">Todo el día</option>
                  {(bloques.data ?? []).map((bloque) => (
                    <option key={bloque.id} value={bloque.codigo}>
                      {bloque.codigo} · {bloque.inicio.slice(0, 5)}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <fieldset className="flex flex-col gap-2">
              <legend className="text-label-xs text-mh-secondary">Días</legend>
              <div className="flex flex-wrap gap-2">
                {DIAS.map((dia, indice) => {
                  const numero = indice + 1;
                  const activo = regla.dias.includes(numero);
                  return (
                    <button
                      key={dia}
                      type="button"
                      aria-pressed={activo}
                      onClick={() => alternarDia(numero)}
                      className={cn(
                        "min-h-[44px] rounded-full border px-4 text-label-xs",
                        activo
                          ? "border-mh-text bg-mh-raised text-mh-text"
                          : "border-mh-border text-mh-secondary hover:bg-mh-raised",
                      )}
                    >
                      {dia}
                    </button>
                  );
                })}
              </div>
            </fieldset>

            <label className="flex min-h-[44px] items-center gap-2 text-label-xs text-mh-secondary">
              <input
                type="checkbox"
                checked={!regla.bloquea}
                onChange={(evento) => actualizar({ bloquea: !evento.target.checked })}
                className="size-5 accent-[var(--mh-accent)]"
              />
              En vez de bloquear, liberar esa franja
            </label>

            <label className="flex flex-col gap-1 text-label-xs text-mh-secondary">
              Motivo (opcional)
              <input
                value={regla.motivo ?? ""}
                onChange={(evento) => actualizar({ motivo: evento.target.value || null })}
                className="min-h-[44px] rounded-sm border border-mh-border-control bg-mh-canvas px-3 text-body-sm text-mh-text"
              />
            </label>

            <div className="flex flex-wrap items-center gap-3">
              <Button
                onClick={() => confirmar.mutate()}
                disabled={
                  !regla.docente_codigo || regla.dias.length === 0 || confirmar.isPending
                }
              >
                <CheckCircle2 aria-hidden="true" />
                {confirmar.isPending ? "Guardando…" : "Confirmar regla"}
              </Button>
              <span aria-live="polite" className="text-label-xs text-mh-secondary">
                {resultado}
              </span>
            </div>
            {confirmar.isError ? <ErrorConsulta error={confirmar.error} /> : null}
          </CardContent>
        </Card>
      ) : null}
    </section>
  );
}
