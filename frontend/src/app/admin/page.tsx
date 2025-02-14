"use client";

import { useState } from "react";
import Header from "@/app/components/Header";
import AdminHeader from "@/app/components/AdminHeader";
import AthleteManagement from "@/app/admin/athletes/AthleteManagement";
import TournamentManagement from "@/app/admin/tournaments/TournamentManagement";
import SettingsManagement from "@/app/admin/settings/SettingsManagement";

const Admin = () => {
  const [currentPage, setCurrentPage] = useState<string>("athletes");

  const handleNavigation = (page: string) => {
    setCurrentPage(page);
  };

  return (
    <div className="text-white min-h-screen bg-dark">
      <Header />
      <AdminHeader onNavigate={handleNavigation} />
      
      <div className="p-8 max-w-7xl mx-auto">
        {currentPage === "athletes" && <AthleteManagement />}
        {currentPage === "tournaments" && <TournamentManagement />}
        {currentPage === "settings" && <SettingsManagement />}
      </div>
    </div>
  );
};

export default Admin;
