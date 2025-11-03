import { useTranslations } from "next-intl";
import Image from "next/image";
import Link from "next/link";

import { ThemeSwitch } from "@/components/theme-switch";
import { Button } from "@/components/ui/button";

interface HeaderProps {
  user?: {
    sub: string;
    role?: string;
  } | null;
}

export function Header({ user }: HeaderProps) {
  const t = useTranslations("Header");
  const isLoggedIn = !!user;
  const buttonLabel = isLoggedIn ? t(user?.role || "admin") : t("login");
  const buttonHref = isLoggedIn ? "/admin" : "/login";

  return (
    <header className="h-16 w-full border-b bg-black">
      <div className="container flex h-full items-center justify-between px-4 md:px-6 lg:px-8">
        <Link href="/" className="flex items-center space-x-2 mt-0.5">
          <Image src="/full_logo.svg" alt="Champion Logo" height={29} width={185} />
        </Link>

        <div className="flex items-center gap-4">
          <ThemeSwitch />
          <Link href={buttonHref}>
            <Button variant="outline">{buttonLabel}</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
