"use client";

import { Button } from "@/components/ui/button";
import { SearchablePicker } from "@/components/admin/searchable-picker";
import { Athlete } from "@/lib/interfaces";
import { useI18n } from "@/lib/i18n";

interface BracketParticipantControlsProps {
  athletes: Athlete[];
  selectedAthleteExternalId: number | null;
  participantSeed: string;
  loading: boolean;
  onSelectAthlete: (value: number) => void;
  onSeedChange: (value: string) => void;
  onAdd: () => void;
}

function getAthleteLabel(athlete: Athlete): string {
  const coachText = Array.isArray(athlete.coaches_last_name)
    ? athlete.coaches_last_name.join(", ")
    : athlete.coaches_last_name;

  return `${athlete.last_name} ${athlete.first_name}${coachText ? ` (${coachText})` : ""}`;
}

export function BracketParticipantControls({
  athletes,
  selectedAthleteExternalId,
  participantSeed,
  loading,
  onSelectAthlete,
  onSeedChange,
  onAdd,
}: BracketParticipantControlsProps) {
  const { t } = useI18n();
  return (
    <div className="admin-card add-participant">
      <div className="admin-card__heading">
        <h2>{t("brackets.addParticipant")}</h2>
        <p>{t("brackets.addHint")}</p>
      </div>

      <div className="add-participant__fields">
        <div className="admin-field">
          <label>{t("common.athlete")}</label>
          <SearchablePicker
            options={athletes.map((athlete) => {
              const externalId = athlete.external_id ?? athlete.id;
              const label = getAthleteLabel(athlete);
              return {
                value: externalId.toString(),
                label,
                keywords: label,
              };
            })}
            value={selectedAthleteExternalId?.toString()}
            placeholder={t("brackets.selectAthlete")}
            searchPlaceholder={t("brackets.searchAthletes")}
            emptyText={t("brackets.noAthletes")}
            onChange={(value) => onSelectAthlete(parseInt(value, 10))}
          />
        </div>

        <div className="admin-field">
          <label htmlFor="participant-seed">{t("brackets.seed")}</label>
          <input
            id="participant-seed"
            className="admin-input"
            placeholder={t("brackets.auto")}
            inputMode="numeric"
            value={participantSeed}
            onChange={(event) => onSeedChange(event.target.value)}
          />
        </div>

        <Button className="add-participant__submit" onClick={onAdd} disabled={loading || !selectedAthleteExternalId}>
          {t("brackets.add")}
        </Button>
      </div>
    </div>
  );
}
