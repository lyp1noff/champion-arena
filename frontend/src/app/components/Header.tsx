"use client";

import Link from "next/link";

const Header = () => {
  return (
    <header className="bg-blue-900 text-white p-2 shadow-md">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="text-3xl font-semibold flex items-center space-x-2">
          <Link href="/">
            <img src="full_logo.svg" alt="Champion Logo" className="h-12" />
          </Link>
        </div>

        <div>
          <Link href="/admin" className="text-secondary hover:text-white transition">
            Админка
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Header;
