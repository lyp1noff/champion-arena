import Link from "next/link";
import Image from "next/image";
import { ModeToggle } from "@/components/mode-toggle";
import { Button } from "@/components/ui/button";
import { useTranslations } from "next-intl";

interface HeaderProps {
  user?: {
    sub: string;
    role?: string;
  } | null;
}

export function Header({ user }: HeaderProps) {
  const t = useTranslations("Header");
  return (
    <header className="sticky top-0 z-40 w-full border-b bg-black">
      <div className="flex h-16 items-center justify-between px-4 md:px-6 lg:container lg:px-8">
        <div className="flex gap-6 md:gap-10 mt-0.5">
          <Link href="/" className="flex items-center space-x-2">
            <Image src="/full_logo.svg" height={29} width={185} alt="Champion Logo" priority />
          </Link>
        </div>
        <div className="flex items-center space-x-4">
          <nav className="flex items-center space-x-4">
            <ModeToggle />
            {user ? (
              <Link href="/admin">
                <Button variant="outline">{t(user.role || "admin")}</Button>
              </Link>
            ) : (
              <Link href="/login">
                <Button variant="outline">{t("login")}</Button>
              </Link>
            )}
          </nav>
        </div>
      </div>
    </header>
  );
}
