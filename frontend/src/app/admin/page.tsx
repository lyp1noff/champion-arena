"use client";

import { useSearchParams, usePathname, useRouter } from "next/navigation";
import { Suspense } from "react";

import Header from "@/app/components/Header";
import AdminHeader from "@/app/components/AdminHeader";
import AthleteManagement from "@/app/admin/athletes/AthleteManagement";
import TournamentManagement from "@/app/admin/tournaments/TournamentManagement";
import SettingsManagement from "@/app/admin/settings/SettingsManagement";

function Page() {
  const searchParams = useSearchParams();
  const currentPage = searchParams.get("page") || "tournaments";
  return (
    <>
      {currentPage === "tournaments" && <TournamentManagement />}
      {currentPage === "athletes" && <AthleteManagement />}
      {currentPage === "settings" && <SettingsManagement />}
    </>
  );
}

const Admin = () => {
  const pathname = usePathname();
  const router = useRouter();

  const handleNavigation = (page: string) => {
    const newUrl = `${pathname}?page=${page}`;
    router.push(newUrl, { scroll: false });
  };

  return (
    <div className="text-white min-h-screen bg-dark">
      <Header />
      <AdminHeader onNavigate={handleNavigation} />

      <div className="p-8 max-w-7xl mx-auto">
        <Suspense fallback={<div>Loading...</div>}>
          <Page />
        </Suspense>
      </div>
    </div>
  );
};

export default Admin;
