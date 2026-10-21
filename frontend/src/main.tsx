import "@fontsource/barlow/600.css";
import "@fontsource/open-sans/400.css";
import "@fontsource/open-sans/600.css";
import "./estilos/tokens.css";
import "./estilos/base.css";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";
import { ProveedorSesion } from "./sesion";

const consultas = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, staleTime: 15_000 } },
});

createRoot(document.getElementById("raiz")!).render(
  <StrictMode>
    <QueryClientProvider client={consultas}>
      <BrowserRouter>
        <ProveedorSesion>
          <App />
        </ProveedorSesion>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
);
