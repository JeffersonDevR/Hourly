import { Outlet } from "react-router-dom";

import { Marca } from "@/components/layout/Marca";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { usaAvisoDeTamano } from "@/lib/media";

/**
 * Shell de la app: alto fijo y **el main es el único que scrollea**. Antes scrolleaba
 * el documento entero, y la barra lateral se estiraba con el contenido: la navegación
 * quedaba fuera de la vista en pantallas largas.
 */
export function AppLayout() {
  const sinSoporte = usaAvisoDeTamano();

  // Diseño §5: por debajo de 768 no se comprime el layout, se avisa.
  if (sinSoporte) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-mh-canvas px-6 text-center">
        <span className="text-mh-text">
          <Marca alto={48} />
        </span>
        <h1 className="text-h2 text-mh-text">Hourly necesita una pantalla más grande</h1>
        <p className="max-w-[46ch] text-body text-mh-secondary">
          Es una herramienta de escritorio para coordinadores: la cuadrícula de cinco días no se
          puede leer en un celular. Abrila en una computadora, o ampliá la ventana.
        </p>
      </main>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-mh-canvas text-mh-text">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <TopBar />
        <main className="mh-scroll-y flex-1 px-4 py-6 md:px-8">
          <div className="mx-auto w-full max-w-[1440px]">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
