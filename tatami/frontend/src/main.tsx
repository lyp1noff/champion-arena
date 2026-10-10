import React from "react";
import ReactDOM from "react-dom/client";

import Home from "@/app/page";
import SetupPage from "@/app/admin/setup/page";
import BracketsAdminPage from "@/app/admin/brackets/page";
import OutboxAdminPage from "@/app/admin/outbox/page";
import TatamiSetupPage from "@/app/admin/tatami/[id]/page";
import ManageTatami from "@/app/admin/tatami/[id]/match/[match_id]/page";
import ScreenTatami from "@/app/screen/page";
import "@/app/globals.css";
import { I18nProvider, LanguageSwitcher, useI18n } from "@/lib/i18n";

function NotFound() {
  const { t } = useI18n();
  return <main className="page-shell"><h1>{t("notFound.title")}</h1><a href="/admin/setup">{t("notFound.openSetup")}</a></main>;
}

function Router() {
  const path = window.location.pathname.replace(/\/+$/, "") || "/";
  if (path === "/screen") return <ScreenTatami />;
  let page: React.ReactNode;
  if (path === "/") page = <Home />;
  else if (path === "/admin/setup") page = <SetupPage />;
  else if (path === "/admin/brackets") page = <BracketsAdminPage />;
  else if (path === "/admin/outbox") page = <OutboxAdminPage />;
  else if (/^\/admin\/tatami\/[^/]+\/match\/[^/]+$/.test(path)) page = <ManageTatami />;
  else if (/^\/admin\/tatami\/[^/]+$/.test(path)) page = <TatamiSetupPage />;
  else page = <NotFound />;
  return <>{page}<LanguageSwitcher /></>;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><I18nProvider><Router /></I18nProvider></React.StrictMode>,
);
