import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { ErrorApi } from "../api";
import { Marca } from "../componentes/Estructura";
import { Aviso, Boton, Campo } from "../componentes/ui";
import { useSesion } from "../sesion";

export function Ingreso() {
  const { yo, vencida, ingresar } = useSesion();
  const navegar = useNavigate();
  const [correo, setCorreo] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  if (yo) return <Navigate to="/clientes" replace />;

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await ingresar(correo, contrasena);
      navegar("/clientes", { replace: true });
    } catch (err) {
      setError(err instanceof ErrorApi ? err.message : "No pudimos ingresar. Probá de nuevo.");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="ingreso">
      <form className="ingreso-tarjeta" onSubmit={enviar} noValidate>
        <div style={{ color: "var(--azul)" }}>
          <Marca />
        </div>
        <h1 style={{ fontSize: 28 }}>Ingresá a tu cuenta</h1>
        {vencida && <Aviso tipo="error">Tu sesión venció. Ingresá de nuevo.</Aviso>}
        {error && <Aviso tipo="error">{error}</Aviso>}
        <Campo
          id="correo"
          etiqueta="Correo"
          type="email"
          autoComplete="username"
          value={correo}
          onChange={(e) => setCorreo(e.target.value)}
          required
        />
        <Campo
          id="contrasena"
          etiqueta="Contraseña"
          type="password"
          autoComplete="current-password"
          value={contrasena}
          onChange={(e) => setContrasena(e.target.value)}
          required
        />
        <Boton type="submit" variante="principal" disabled={enviando || !correo || !contrasena}>
          {enviando ? "Ingresando" : "Ingresar"}
        </Boton>
      </form>
    </div>
  );
}
