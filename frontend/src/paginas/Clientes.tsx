import { useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { flexRender, getCoreRowModel, useReactTable, type ColumnDef } from "@tanstack/react-table";
import { api, type ClienteLista } from "../api";
import { Boton, Campo, Chip, EstadoConsulta, Vacio } from "../componentes/ui";

export function Clientes() {
  const [texto, setTexto] = useState("");
  const [busqueda, setBusqueda] = useState("");
  const consulta = useQuery({ queryKey: ["clientes", busqueda], queryFn: () => api.clientes(busqueda), retry: false });

  const columnas = useMemo<ColumnDef<ClienteLista>[]>(
    () => [
      {
        header: "Cliente",
        cell: ({ row }) => <Link to={`/clientes/${row.original.id}`}>{row.original.nombre}</Link>,
      },
      {
        header: "CUIT",
        cell: ({ row }) => (
          <ul className="lista-simple">
            {row.original.contribuyentes.map((c) => (
              <li key={c.id} className="cuit">
                {c.cuit_enmascarado}
              </li>
            ))}
          </ul>
        ),
      },
      { header: "Área", accessorKey: "area_etiqueta" },
      { header: "Responsable", cell: ({ row }) => row.original.responsable?.nombre ?? "Sin responsable" },
      {
        header: "Estado",
        cell: ({ row }) =>
          row.original.activo ? <Chip color="correcto">Activo</Chip> : <Chip color="neutro">De baja</Chip>,
      },
    ],
    [],
  );

  const tabla = useReactTable({
    data: consulta.data ?? [],
    columns: columnas,
    getCoreRowModel: getCoreRowModel(),
  });

  function buscar(e: FormEvent) {
    e.preventDefault();
    setBusqueda(texto.trim());
  }

  return (
    <>
      <div className="encabezado-pantalla">
        <h1>Clientes</h1>
      </div>
      <form className="barra-busqueda" onSubmit={buscar} role="search">
        <Campo
          id="buscar"
          etiqueta="Buscar por nombre"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          placeholder="Por ejemplo, Ejemplo S.A."
        />
        <Boton type="submit">Buscar</Boton>
        {busqueda && (
          <Boton
            variante="discreto"
            onClick={() => {
              setTexto("");
              setBusqueda("");
            }}
          >
            Borrar búsqueda
          </Boton>
        )}
      </form>
      <EstadoConsulta
        consulta={consulta}
        vacio={
          <Vacio
            titulo={busqueda ? "No hay resultados" : "Todavía no hay clientes"}
            texto={
              busqueda
                ? "Probá con otra parte del nombre."
                : "Cuando haya clientes asignados a vos, los vas a ver acá."
            }
          />
        }
      >
        <div className="tabla-caja">
          <table className="tabla">
            <thead>
              {tabla.getHeaderGroups().map((g) => (
                <tr key={g.id}>
                  {g.headers.map((h) => (
                    <th key={h.id} scope="col">
                      {flexRender(h.column.columnDef.header, h.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {tabla.getRowModel().rows.map((fila) => (
                <tr key={fila.id}>
                  {fila.getVisibleCells().map((celda) => (
                    <td key={celda.id}>{flexRender(celda.column.columnDef.cell, celda.getContext())}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </EstadoConsulta>
    </>
  );
}
