// Componentes reutilizables. Los estilos están en estilos/base.css y usan los tokens de tokens.css.
import type { ButtonHTMLAttributes, ReactNode, SelectHTMLAttributes, InputHTMLAttributes } from "react";
import { Link } from "react-router-dom";
import { ErrorApi } from "../api";

// ---------- Botones ----------
type Variante = "principal" | "contorno" | "discreto";

export function Boton({
  variante = "contorno",
  className = "",
  ...resto
}: ButtonHTMLAttributes<HTMLButtonElement> & { variante?: Variante }) {
  return <button type="button" className={`boton boton-${variante} ${className}`} {...resto} />;
}

export function EnlaceBoton({ a, variante = "contorno", children }: { a: string; variante?: Variante; children: ReactNode }) {
  return (
    <Link to={a} className={`boton boton-${variante}`}>
      {children}
    </Link>
  );
}

// ---------- Campos ----------
interface CampoBase {
  id: string;
  etiqueta: string;
  ayuda?: string;
  error?: string | null;
}

export function Campo({ id, etiqueta, ayuda, error, ...resto }: CampoBase & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="campo">
      <label htmlFor={id}>{etiqueta}</label>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : ayuda ? `${id}-ayuda` : undefined}
        {...resto}
      />
      {ayuda && !error && (
        <span className="ayuda" id={`${id}-ayuda`}>
          {ayuda}
        </span>
      )}
      {error && (
        <span className="error-campo" id={`${id}-error`}>
          {error}
        </span>
      )}
    </div>
  );
}

export function Desplegable({
  id,
  etiqueta,
  opciones,
  ...resto
}: CampoBase & { opciones: [string, string][] } & SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <div className="campo">
      <label htmlFor={id}>{etiqueta}</label>
      <select id={id} {...resto}>
        {opciones.map(([valor, texto]) => (
          <option key={valor} value={valor}>
            {texto}
          </option>
        ))}
      </select>
    </div>
  );
}

// ---------- Chip de estado (siempre lleva texto) ----------
export type ColorChip = "correcto" | "atencion" | "error" | "neutro";

export function Chip({ color, children }: { color: ColorChip; children: ReactNode }) {
  return <span className={`chip chip-${color}`}>{children}</span>;
}

// ---------- Estados de pantalla ----------
export function Cargando({ texto = "Cargando" }: { texto?: string }) {
  return (
    <div className="cargando" role="status" aria-live="polite">
      <span className="sr-only" style={{ position: "absolute", left: -9999 }}>
        {texto}
      </span>
      <div className="barra-gris" style={{ width: "40%" }} />
      <div className="barra-gris" />
      <div className="barra-gris" />
      <div className="barra-gris" style={{ width: "70%" }} />
    </div>
  );
}

export function Vacio({ titulo, texto, children }: { titulo: string; texto?: string; children?: ReactNode }) {
  return (
    <div className="estado-caja">
      <h2>{titulo}</h2>
      {texto && <p>{texto}</p>}
      {children}
    </div>
  );
}

export function ErrorConReintento({ error, alReintentar }: { error: unknown; alReintentar: () => void }) {
  const mensaje = error instanceof ErrorApi ? error.message : "No pudimos cargar esta pantalla.";
  return (
    <div className="estado-caja" role="alert">
      <h2>No se pudo cargar</h2>
      <p>{mensaje}</p>
      <Boton variante="principal" onClick={alReintentar}>
        Reintentar
      </Boton>
    </div>
  );
}

export function SinAcceso() {
  return (
    <div className="estado-caja">
      <h2>No tenés acceso a esta pantalla</h2>
      <p>Si lo necesitás para tu trabajo, pedíselo a un socio del estudio.</p>
      <EnlaceBoton a="/clientes">Volver al inicio</EnlaceBoton>
    </div>
  );
}

export function SesionVencida() {
  return (
    <div className="estado-caja">
      <h2>Tu sesión venció</h2>
      <p>Por seguridad, la sesión se cierra sola. Ingresá de nuevo para seguir.</p>
      <EnlaceBoton a="/ingreso" variante="principal">
        Ingresar
      </EnlaceBoton>
    </div>
  );
}

export function Aviso({ tipo, children }: { tipo: "correcto" | "error"; children: ReactNode }) {
  return (
    <div className={`aviso aviso-${tipo}`} role={tipo === "error" ? "alert" : "status"}>
      {children}
    </div>
  );
}

// Elige qué mostrar según el estado de una consulta (cargando, error, sin acceso, vacío).
export function EstadoConsulta({
  consulta,
  vacio,
  children,
}: {
  consulta: { isLoading: boolean; isError: boolean; error: unknown; refetch: () => unknown; data: unknown };
  vacio?: ReactNode;
  children: ReactNode;
}) {
  if (consulta.isLoading) return <Cargando />;
  if (consulta.isError) {
    const e = consulta.error;
    if (e instanceof ErrorApi && e.estado === 403) return <SinAcceso />;
    return <ErrorConReintento error={e} alReintentar={() => consulta.refetch()} />;
  }
  if (vacio && Array.isArray(consulta.data) && consulta.data.length === 0) return <>{vacio}</>;
  return <>{children}</>;
}
