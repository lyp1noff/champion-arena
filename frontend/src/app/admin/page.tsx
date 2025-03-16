import Link from "next/link";
import { Button } from "@/components/ui/button";
import { useTranslations } from "next-intl";

export default function Admin() {
  const t = useTranslations("Admin");

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
      </div>
    </div>
  );
}
