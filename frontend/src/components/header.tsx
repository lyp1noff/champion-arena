import Link from "next/link";
import Image from "next/image";
import { ModeToggle } from "@/components/mode-toggle";
import { Button } from "@/components/ui/button";

export function Header() {
  return (
    <header className="sticky top-0 z-40 w-full border-b bg-black">
      <div className="flex h-16 items-center justify-between px-4 md:px-6 lg:container lg:px-8">
        <div className="flex gap-6 md:gap-10 mt-0.5">
          <Link href="/" className="flex items-center space-x-2">
            <Image src="/full_logo.svg" height={29} width={185} alt="Champion Logo" placeholder="empty" />
          </Link>
        </div>
        <div className="flex items-center space-x-4">
          <nav className="flex items-center space-x-4">
            <ModeToggle />
            <Link href="/admin">
              <Button variant="outline">Login</Button>
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
}
