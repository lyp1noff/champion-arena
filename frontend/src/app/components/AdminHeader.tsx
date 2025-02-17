"use client";

interface AdminHeaderProps {
  onNavigate: (page: string) => void;
}

const AdminHeader = ({ onNavigate }: AdminHeaderProps) => {
  return (
    <header className="bg-primary text-white p-2 shadow-md mx-auto flex justify-between items-center">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <nav className="space-x-6">
          <button className="text-secondary hover:text-accent transition" onClick={() => onNavigate("tournaments")}>
            Турниры
          </button>
          <button className="text-secondary hover:text-accent transition" onClick={() => onNavigate("athletes")}>
            Спортсмены
          </button>
          <button className="text-secondary hover:text-accent transition" onClick={() => onNavigate("settings")}>
            Настройки
          </button>
        </nav>
      </div>
    </header>
  );
};

export default AdminHeader;
