"use client";

import { useState } from "react";
import Header from "@/app/components/Header";
import AdminHeader from "@/app/components/AdminHeader";

const Admin = () => {
  const [currentPage, setCurrentPage] = useState<string>("tournaments");

  const handleNavigation = (page: string) => {
    setCurrentPage(page);
  };

  return (
    <div className="text-white min-h-screen bg-dark">
      <Header />
      <AdminHeader onNavigate={handleNavigation} />
      
      <div className="p-8">
        {currentPage === "athletes" && (
          <div>
            <h1 className="text-4xl font-bold text-center text-secondary">Управление атлетами</h1>
            <p className="mt-4 text-xl text-center">Здесь будет интерфейс для управления атлетами.</p>
          </div>
        )}
        {currentPage === "tournaments" && (
          <div>
            <h1 className="text-4xl font-bold text-center text-secondary">Управление турнирами</h1>
            <p className="mt-4 text-xl text-center">Здесь будет интерфейс для управления турнирами.</p>
          </div>
        )}
        {currentPage === "settings" && (
          <div>
            <h1 className="text-4xl font-bold text-center text-secondary">Настройки</h1>
            <p className="mt-4 text-xl text-center">Здесь будут настройки админки.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Admin;
