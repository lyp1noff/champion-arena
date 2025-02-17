"use client";

import Link from "next/link";
import Image from "next/image";

const Header = () => {
  return (
    <header className="bg-sky-950 text-white p-2 shadow-md">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <div className="text-3xl font-semibold flex items-center space-x-2">
          <Link href="/">
            <Image src="full_logo.svg" height={48} width={210} alt="Champion Logo" />
          </Link>
        </div>

        <div>
          <Link href="/admin" className="text-secondary hover:text-accent transition">
            Админка
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Header;
