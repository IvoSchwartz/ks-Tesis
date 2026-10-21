import { NavLink, Navigate, Outlet } from "react-router-dom";
import { useSesion } from "../sesion";
import { Boton, Cargando, SesionVencida } from "./ui";

export function Marca() {
  return (
    <div className="marca">
      {/* Monograma de texto: reemplazar por el logo en vector cuando lo entregue el estudio */}
      <span className="monograma" aria-hidden="true">
        K&amp;S
      </span>
      <span>Impuestos</span>
    </div>
  );
}

export function Estructura() {
  const { yo, cargando, vencida, salir } = useSesion();

  if (cargando) {
    return (
      <div className="contenido">
        <Cargando texto="Entrando" />
      </div>
    );
  }
  if (!yo) {
    if (vencida) {
      return (
        <div className="contenido">
          <SesionVencida />
        </div>
      );
    }
    return <Navigate to="/ingreso" replace />;
  }

  return (
    <div className="estructura">
      <aside className="menu">
        <Marca />
        {/* El menú viene del servidor (/me): ahí está la única tabla de permisos */}
        <nav aria-label="Principal">
          {yo.menu.map((item) => (
            <NavLink key={item.clave} to={item.ruta} className={({ isActive }) => (isActive ? "activo" : "")}>
              {item.etiqueta}
            </NavLink>
          ))}
        </nav>
        <div className="menu-pie">
          <div>
            <strong>{yo.nombre}</strong>
            <br />
            {yo.rol_etiqueta} · {yo.area_etiqueta}
          </div>
          <Boton onClick={salir}>Salir</Boton>
        </div>
      </aside>
      <main className="contenido">
        <Outlet />
      </main>
    </div>
  );
}
