import { ExternalMatch } from "@/lib/interfaces";
import { useI18n } from "@/lib/i18n";

interface MatchInfoProps {
  currentMatch: ExternalMatch | null;
  matchId: string;
  tatamiId: string;
}

export function MatchInfo({ currentMatch, matchId, tatamiId }: MatchInfoProps) {
  const { t } = useI18n();
  return (
    <div className="border rounded-lg p-4 bg-blue-50">
      <h3 className="text-lg font-semibold mb-2">{t("match.current")}</h3>
      {currentMatch ? (
        <div className="space-y-2">
          <div>
            <strong>{t("tatami.athlete1")}:</strong>{" "}
            {currentMatch.athlete1
              ? `${currentMatch.athlete1.last_name} ${currentMatch.athlete1.first_name} (${currentMatch.athlete1.coaches_last_name})`
              : t("match.tbd")}
          </div>
          <div>
            <strong>{t("tatami.athlete2")}:</strong>{" "}
            {currentMatch.athlete2
              ? `${currentMatch.athlete2.last_name} ${currentMatch.athlete2.first_name} (${currentMatch.athlete2.coaches_last_name})`
              : t("match.tbd")}
          </div>
          <div>
            <strong>{t("common.status")}:</strong> {currentMatch.status}
          </div>
          <div>
            <strong>{t("match.id")}:</strong> {matchId}
          </div>
        </div>
      ) : (
        <div className="text-gray-600">
          {t("match.noSelection")}{" "}
          <a href={`/admin/tatami/${tatamiId}`} className="text-blue-600 underline">
            {t("match.setup")}
          </a>{" "}
        </div>
      )}
    </div>
  );
}
