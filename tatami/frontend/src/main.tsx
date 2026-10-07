import React from "react";
import ReactDOM from "react-dom/client";

import Home from "@/app/page";
import SetupPage from "@/app/admin/setup/page";
import BracketsAdminPage from "@/app/admin/brackets/page";
import TatamiSetupPage from "@/app/admin/tatami/[id]/page";
import ManageTatami from "@/app/admin/tatami/[id]/match/[match_id]/page";
import ScreenTatami from "@/app/screen/tatami/[id]/page";
import "@/app/globals.css";

function NotFound() {
  return <main className="page-shell"><h1>Page not found</h1><a href="/admin/setup">Open Tatami setup</a></main>;
}

function Router() {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  if (path === "/") return <Home />;
  if (path === "/admin/setup") return <SetupPage />;
  if (path === "/admin/brackets") return <BracketsAdminPage />;
  if (/^\/screen\/tatami\/[^/]+$/.test(path)) return <ScreenTatami />;
  if (/^\/admin\/tatami\/[^/]+\/match\/[^/]+$/.test(path)) return <ManageTatami />;
  if (/^\/admin\/tatami\/[^/]+$/.test(path)) return <TatamiSetupPage />;
  return <NotFound />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><Router /></React.StrictMode>);
