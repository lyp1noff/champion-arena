"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useTranslations } from "next-intl";
import { logout } from "@/lib/api/auth";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

export default function Admin() {
  const t = useTranslations("Admin");
  const router = useRouter();

  const handleLogout = async () => {
    try {
      await logout();
      router.push("/");
      router.refresh();
    } catch {
      toast.error("Logout failed");
    }
  };

  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-4">{t("title")}</h1>
      <div className="flex space-x-4">
        <Link href="/admin/tournaments">
          <Button>{t("tournaments")}</Button>
        </Link>
        <Link href="/admin/athletes">
          <Button>{t("athletes")}</Button>
        </Link>
        <Button variant="outline" onClick={handleLogout}>
          Logout
        </Button>
      </div>
    </div>
  );
}
