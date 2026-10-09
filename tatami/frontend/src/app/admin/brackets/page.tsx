import { BracketAdmin } from "@/components/admin/bracket-admin";
import { useI18n } from "@/lib/i18n";

export default function BracketsAdminPage() {
  const { t } = useI18n();
  return (
    <main className="admin-page">
      <div className="admin-page__content admin-page__content--wide">
        <nav className="admin-page__nav">
          <a href="/admin/setup">← {t("brackets.back")}</a>
        </nav>
        <BracketAdmin />
      </div>
    </main>
  );
}
