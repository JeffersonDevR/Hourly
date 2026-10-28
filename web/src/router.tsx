import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { Conflictos } from "@/pages/Conflictos";
import { Cursos } from "@/pages/Cursos";
import { Docentes } from "@/pages/Docentes";
import { Horario } from "@/pages/Horario";
import { Importar } from "@/pages/Importar";
import { Inicio } from "@/pages/Inicio";
import { NoEncontrada } from "@/pages/NoEncontrada";
import { Publicacion } from "@/pages/Publicacion";
import { Recursos } from "@/pages/Recursos";
import { Reglas } from "@/pages/Reglas";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Inicio /> },
      { path: "importar", element: <Importar /> },
      { path: "cursos", element: <Cursos /> },
      { path: "docentes", element: <Docentes /> },
      { path: "recursos", element: <Recursos /> },
      { path: "reglas", element: <Reglas /> },
      { path: "horario", element: <Horario /> },
      { path: "conflictos", element: <Conflictos /> },
      { path: "publicacion", element: <Publicacion /> },
      { path: "*", element: <NoEncontrada /> },
    ],
  },
]);
