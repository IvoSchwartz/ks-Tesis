import { Navigate, Route, Routes } from "react-router-dom";
import { Estructura } from "./componentes/Estructura";
import { FichaCliente } from "./paginas/FichaCliente";
import { Clientes } from "./paginas/Clientes";
import { Ingreso } from "./paginas/Ingreso";
import { Usuarios } from "./paginas/Usuarios";

export function App() {
  return (
    <Routes>
      <Route path="/ingreso" element={<Ingreso />} />
      <Route element={<Estructura />}>
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/clientes/:id" element={<FichaCliente />} />
        <Route path="/usuarios" element={<Usuarios />} />
      </Route>
      <Route path="*" element={<Navigate to="/clientes" replace />} />
    </Routes>
  );
}
