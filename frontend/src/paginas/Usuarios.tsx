import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AREAS, ROLES, ErrorApi, api, type Usuario } from "../api";
import { Aviso, Boton, Campo, Chip, Desplegable, EstadoConsulta } from "../componentes/ui";

const VACIO = { nombre: "", correo: "", contrasena: "", area: "impuestos", rol: "empleado_impuestos" };

export function Usuarios() {
  const cliente = useQueryClient();
  const consulta = useQuery({ queryKey: ["usuarios"], queryFn: api.usuarios, retry: false });
  const [form, setForm] = useState(VACIO);
  const [aviso, setAviso] = useState<{ tipo: "correcto" | "error"; texto: string } | null>(null);

  const refrescar = () => cliente.invalidateQueries({ queryKey: ["usuarios"] });
  const mensaje = (e: unknown) => (e instanceof ErrorApi ? e.message : "No pudimos completar la acción.");

  const crear = useMutation({
    mutationFn: () => api.crearUsuario(form),
    onSuccess: () => {
      setAviso({ tipo: "correcto", texto: "Se guardó la persona." });
      setForm(VACIO);
      refrescar();
    },
    onError: (e) => setAviso({ tipo: "error", texto: mensaje(e) }),
  });

  const cambiarEstado = useMutation({
    mutationFn: (u: Usuario) => (u.activo ? api.darDeBaja(u.id) : api.cambiarUsuario(u.id, { activo: true })),
    onSuccess: (u) => {
      setAviso({ tipo: "correcto", texto: u.activo ? "Se reactivó la persona." : "Se dio de baja a la persona." });
      refrescar();
    },
    onError: (e) => setAviso({ tipo: "error", texto: mensaje(e) }),
  });

  function enviar(e: FormEvent) {
    e.preventDefault();
    setAviso(null);
    crear.mutate();
  }
  const campo = (k: keyof typeof VACIO) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });

  return (
    <>
      <div className="encabezado-pantalla">
        <h1>Usuarios</h1>
      </div>
      {aviso && <Aviso tipo={aviso.tipo}>{aviso.texto}</Aviso>}

      <EstadoConsulta consulta={consulta}>
        <div className="tabla-caja">
          <table className="tabla">
            <thead>
              <tr>
                <th scope="col">Nombre</th>
                <th scope="col">Correo</th>
                <th scope="col">Área</th>
                <th scope="col">Rol</th>
                <th scope="col">Estado</th>
                <th scope="col">Acción</th>
              </tr>
            </thead>
            <tbody>
              {(consulta.data ?? []).map((u) => (
                <tr key={u.id}>
                  <td>{u.nombre}</td>
                  <td>{u.correo}</td>
                  <td>{u.area_etiqueta}</td>
                  <td>{u.rol_etiqueta}</td>
                  <td>{u.activo ? <Chip color="correcto">Activo</Chip> : <Chip color="neutro">De baja</Chip>}</td>
                  <td>
                    <Boton
                      variante="discreto"
                      disabled={cambiarEstado.isPending}
                      onClick={() => {
                        setAviso(null);
                        cambiarEstado.mutate(u);
                      }}
                    >
                      {u.activo ? "Dar de baja" : "Reactivar"}
                    </Boton>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <form className="panel" onSubmit={enviar} aria-labelledby="nuevo">
          <h2 id="nuevo">Agregar persona</h2>
          <div className="formulario-grilla">
            <Campo id="nombre" etiqueta="Nombre y apellido" value={form.nombre} onChange={campo("nombre")} required />
            <Campo id="correo-nuevo" etiqueta="Correo" type="email" value={form.correo} onChange={campo("correo")} required />
            <Campo
              id="contrasena-nueva"
              etiqueta="Contraseña inicial"
              type="password"
              autoComplete="new-password"
              ayuda="Al menos 10 caracteres."
              value={form.contrasena}
              onChange={campo("contrasena")}
              required
            />
            <Desplegable id="area" etiqueta="Área" opciones={AREAS} value={form.area} onChange={campo("area")} />
            <Desplegable id="rol" etiqueta="Rol" opciones={ROLES} value={form.rol} onChange={campo("rol")} />
          </div>
          <div className="acciones">
            <Boton
              type="submit"
              variante="principal"
              disabled={crear.isPending || !form.nombre || !form.correo || form.contrasena.length < 10}
            >
              {crear.isPending ? "Guardando" : "Guardar persona"}
            </Boton>
          </div>
        </form>
      </EstadoConsulta>
    </>
  );
}
