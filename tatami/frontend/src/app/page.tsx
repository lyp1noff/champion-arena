import { useI18n } from "@/lib/i18n";

export default function Home() {
  const { t } = useI18n();
  return (
    <div className="p-10">
      <a className="text-xl" href="admin/setup">
        {t("home.openSetup")}
      </a>
    </div>
  );
}
