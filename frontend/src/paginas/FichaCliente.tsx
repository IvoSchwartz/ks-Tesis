import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CONDICIONES, TIPOS, api, formatearCuit } from "../api";
import { Chip, EstadoConsulta } from "../componentes/ui";

export function FichaCliente() {
  const { id } = useParams();
  const numero = Number(id);
  const consulta = useQuery({
    queryKey: ["cliente", numero],
    queryFn: () => api.cliente(numero),
    enabled: Number.isInteger(numero) && numero > 0,
    retry: false,
  });
  const c = consulta.data;

  return (
    <>
      <p style={{ margin: 0 }}>
        <Link to="/clientes">Volver a clientes</Link>
      </p>
      <EstadoConsulta consulta={consulta}>
        {c && (
          <>
            <div className="encabezado-pantalla">
              <h1>{c.nombre}</h1>
              {c.activo ? <Chip color="correcto">Activo</Chip> : <Chip color="neutro">De baja</Chip>}
            </div>
            <section className="panel" aria-labelledby="datos">
              <h2 id="datos">Datos del cliente</h2>
              <dl className="datos">
                <div>
                  <dt>Área</dt>
                  <dd>{c.area_etiqueta}</dd>
                </div>
                <div>
                  <dt>Responsable</dt>
                  <dd>{c.responsable?.nombre ?? "Sin responsable"}</dd>
                </div>
              </dl>
            </section>
            <section aria-labelledby="cuits" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <h2 id="cuits">CUIT del cliente</h2>
              <div className="tabla-caja">
                <table className="tabla">
                  <thead>
                    <tr>
                      <th scope="col">CUIT</th>
                      <th scope="col">Nombre</th>
                      <th scope="col">Tipo</th>
                      <th scope="col">Condición</th>
                    </tr>
                  </thead>
                  <tbody>
                    {c.contribuyentes.map((k) => (
                      <tr key={k.id}>
                        <td className="cuit">{formatearCuit(k.cuit)}</td>
                        <td>{k.nombre}</td>
                        <td>{TIPOS[k.tipo] ?? k.tipo}</td>
                        <td>{CONDICIONES[k.condicion] ?? k.condicion}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        )}
      </EstadoConsulta>
    </>
  );
}
