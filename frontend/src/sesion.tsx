import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, borrarToken, configurarVencimiento, guardarToken, leerToken, type Yo } from "./api";

interface Sesion {
  yo: Yo | null;
  cargando: boolean;
  vencida: boolean;
  ingresar: (correo: string, contrasena: string) => Promise<void>;
  salir: () => void;
}

const Contexto = createContext<Sesion | null>(null);

export function ProveedorSesion({ children }: { children: ReactNode }) {
  const cliente = useQueryClient();
  const [hayToken, setHayToken] = useState<boolean>(() => leerToken() !== null);
  const [vencida, setVencida] = useState(false);

  const cerrar = useCallback(() => {
    borrarToken();
    setHayToken(false);
    cliente.clear();
  }, [cliente]);

  useEffect(() => {
    configurarVencimiento(() => {
      setVencida(true);
      cerrar();
    });
  }, [cerrar]);

  const consulta = useQuery({ queryKey: ["yo"], queryFn: api.yo, enabled: hayToken, retry: false });

  const ingresar = useCallback(
    async (correo: string, contrasena: string) => {
      const r = await api.ingresar(correo, contrasena);
      guardarToken(r.access_token);
      setVencida(false);
      setHayToken(true);
      await cliente.invalidateQueries({ queryKey: ["yo"] });
    },
    [cliente],
  );

  const valor = useMemo<Sesion>(
    () => ({
      yo: hayToken ? (consulta.data ?? null) : null,
      cargando: hayToken && consulta.isLoading,
      vencida,
      ingresar,
      salir: cerrar,
    }),
    [hayToken, consulta.data, consulta.isLoading, vencida, ingresar, cerrar],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useSesion(): Sesion {
  const v = useContext(Contexto);
  if (!v) throw new Error("useSesion fuera del proveedor");
  return v;
}
