// Cliente de la API. Toda la comunicación con el backend pasa por acá.

const URL_API = (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
const CLAVE_TOKEN = "ks_token";

export class ErrorApi extends Error {
  estado: number;
  constructor(estado: number, mensaje: string) {
    super(mensaje);
    this.estado = estado;
  }
}

// El token vive en sessionStorage: se pierde al cerrar la pestaña.
export function leerToken(): string | null {
  try {
    return sessionStorage.getItem(CLAVE_TOKEN);
  } catch {
    return null;
  }
}
export function guardarToken(token: string): void {
  try {
    sessionStorage.setItem(CLAVE_TOKEN, token);
  } catch {
    /* sin almacenamiento: la sesión dura hasta recargar */
  }
}
export function borrarToken(): void {
  try {
    sessionStorage.removeItem(CLAVE_TOKEN);
  } catch {
    /* nada que borrar */
  }
}

// Cuando el servidor responde 401 con una sesión abierta, se avisa a la aplicación.
let alVencerSesion: () => void = () => {};
export function configurarVencimiento(funcion: () => void): void {
  alVencerSesion = funcion;
}

function mensajeDe(cuerpo: unknown, estado: number): string {
  const detalle = (cuerpo as { detail?: unknown } | null)?.detail;
  if (typeof detalle === "string") return detalle;
  if (Array.isArray(detalle)) return "Revisá los datos: hay campos que no son válidos.";
  if (estado >= 500) return "Algo falló de nuestro lado. Probá de nuevo en un momento.";
  return "No pudimos completar la acción.";
}

export async function pedir<T>(ruta: string, opciones: { metodo?: string; cuerpo?: unknown } = {}): Promise<T> {
  const cabeceras: Record<string, string> = {};
  const token = leerToken();
  if (token) cabeceras["Authorization"] = `Bearer ${token}`;
  if (opciones.cuerpo !== undefined) cabeceras["Content-Type"] = "application/json";

  let respuesta: Response;
  try {
    respuesta = await fetch(`${URL_API}${ruta}`, {
      method: opciones.metodo ?? "GET",
      headers: cabeceras,
      body: opciones.cuerpo !== undefined ? JSON.stringify(opciones.cuerpo) : undefined,
    });
  } catch {
    throw new ErrorApi(0, "No pudimos conectarnos. Revisá tu conexión y probá de nuevo.");
  }

  let cuerpo: unknown = null;
  try {
    cuerpo = await respuesta.json();
  } catch {
    /* respuesta sin cuerpo */
  }

  if (!respuesta.ok) {
    // 401 con sesión abierta = la sesión venció. En el ingreso, 401 es "datos incorrectos".
    if (respuesta.status === 401 && token) alVencerSesion();
    throw new ErrorApi(respuesta.status, mensajeDe(cuerpo, respuesta.status));
  }
  return cuerpo as T;
}

// ---------- Tipos ----------
export interface ItemMenu {
  clave: string;
  etiqueta: string;
  ruta: string;
}
export interface Yo {
  id: number;
  nombre: string;
  correo: string;
  area: string;
  area_etiqueta: string;
  rol: string;
  rol_etiqueta: string;
  alcance: string;
  capacidades: string[];
  menu: ItemMenu[];
}
export interface Persona {
  id: number;
  nombre: string;
}
export interface ContribuyenteLista {
  id: number;
  cuit_enmascarado: string;
  nombre: string;
  tipo: string;
  condicion: string;
}
export interface ContribuyenteFicha {
  id: number;
  cuit: string;
  nombre: string;
  tipo: string;
  condicion: string;
}
export interface ClienteLista {
  id: number;
  nombre: string;
  area: string;
  area_etiqueta: string;
  activo: boolean;
  responsable: Persona | null;
  contribuyentes: ContribuyenteLista[];
}
export interface ClienteFicha {
  id: number;
  nombre: string;
  area: string;
  area_etiqueta: string;
  activo: boolean;
  responsable: Persona | null;
  contribuyentes: ContribuyenteFicha[];
}
export interface Usuario {
  id: number;
  nombre: string;
  correo: string;
  area: string;
  area_etiqueta: string;
  rol: string;
  rol_etiqueta: string;
  activo: boolean;
}
export interface UsuarioNuevo {
  nombre: string;
  correo: string;
  contrasena: string;
  area: string;
  rol: string;
}

// ---------- Llamadas ----------
export const api = {
  ingresar: (correo: string, contrasena: string) =>
    pedir<{ access_token: string }>("/auth/login", { metodo: "POST", cuerpo: { correo, contrasena } }),
  yo: () => pedir<Yo>("/me"),
  clientes: (q: string) => pedir<ClienteLista[]>(`/clientes${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  cliente: (id: number) => pedir<ClienteFicha>(`/clientes/${id}`),
  usuarios: () => pedir<Usuario[]>("/usuarios"),
  crearUsuario: (datos: UsuarioNuevo) => pedir<Usuario>("/usuarios", { metodo: "POST", cuerpo: datos }),
  cambiarUsuario: (id: number, datos: Partial<{ activo: boolean }>) =>
    pedir<Usuario>(`/usuarios/${id}`, { metodo: "PUT", cuerpo: datos }),
  darDeBaja: (id: number) => pedir<Usuario>(`/usuarios/${id}`, { metodo: "DELETE" }),
};

// Opciones de los desplegables (las claves son las de la base; las etiquetas, para mostrar).
export const AREAS: [string, string][] = [
  ["impuestos", "Impuestos"],
  ["secretaria", "Secretaría"],
  ["laboral", "Laboral"],
  ["contabilidad_auditoria", "Contabilidad y Auditoría"],
];
export const ROLES: [string, string][] = [
  ["admin_socio", "Administrador/Socio"],
  ["responsable_area", "Responsable de área"],
  ["empleado_impuestos", "Empleado de Impuestos"],
  ["secretaria", "Secretaría"],
];
export const CONDICIONES: Record<string, string> = {
  responsable_inscripto: "Responsable inscripto",
  monotributista: "Monotributista",
  otro: "Otro",
};
export const TIPOS: Record<string, string> = { humana: "Persona humana", juridica: "Persona jurídica" };

export function formatearCuit(c: string): string {
  return c.length === 11 ? `${c.slice(0, 2)}-${c.slice(2, 10)}-${c.slice(10)}` : c;
}
