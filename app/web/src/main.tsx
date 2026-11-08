import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider, createBrowserRouter } from "react-router-dom";

import { Layout } from "./Layout";
import { SearchPage } from "./pages/SearchPage";
import { SettlementPage } from "./pages/SettlementPage";
import "./styles.css";

const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: "/", element: <SearchPage /> },
      { path: "/settlements/:code", element: <SettlementPage /> },
      { path: "*", element: <SearchPage /> },
    ],
  },
]);

const root = document.getElementById("root");
if (!root) throw new Error("index.html is missing #root");
createRoot(root).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);
