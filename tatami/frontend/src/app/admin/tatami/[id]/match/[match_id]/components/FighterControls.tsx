import { Button } from "@/components/ui/button";
import { ExternalMatch } from "@/lib/interfaces";
import { useI18n } from "@/lib/i18n";
import { MATCH_STATUS } from "@/lib/interfaces";

interface FighterControlsProps {
  currentMatch: ExternalMatch | null;
  score1: number;
  score2: number;
  shido1: number;
  shido2: number;
  senshu: number;
  swap_status: boolean;
  onAdjustScore: (fighter: 1 | 2, delta: number) => void;
  onSetShido: (fighter: 1 | 2, value: number) => void;
  onSetSenshu: (fighter_or_zero: 0 | 1 | 2) => void;
}

export function FighterControls({
  currentMatch,
  score1,
  score2,
  shido1,
  shido2,
  senshu,
  swap_status,
  onAdjustScore,
  onSetShido,
  onSetSenshu,
}: FighterControlsProps) {
  const { t } = useI18n();
  const fighters = swap_status ? [2, 1] : [1, 2];
  const disabled = currentMatch?.status !== MATCH_STATUS.STARTED;

  return (
    <div className="fighter-grid">
      {fighters.map((id) => {
        const athlete = id === 1 ? currentMatch?.athlete1 : currentMatch?.athlete2;
        const coaches = athlete?.coaches_last_name as string[] | string | undefined;
        const coach = Array.isArray(coaches) ? coaches.filter(Boolean).join(", ") : coaches?.trim();
        const athleteName = athlete
          ? `${athlete.last_name} ${athlete.first_name}${coach ? ` · ${coach}` : ""}`
          : t("match.fighter", { id });

        return (
          <section key={id} className={`fighter-card ${id === 1 ? "fighter-card--red" : "fighter-card--blue"}`}>
            <h2 className="fighter-card__name">{athleteName}</h2>

            {/* Score */}
            <div className="fighter-score">
              <div className="fighter-score__heading">
                <Button
                  disabled={disabled}
                  variant="outline"
                  onClick={() => onSetSenshu(senshu === id ? 0 : (id as 1 | 2))}
                  className={senshu === id ? "senshu-button is-active" : "senshu-button"}
                  title="Senshu"
                >
                  S
                </Button>
                <div className="fighter-score__value">
                  <span>{t("match.score")}</span>
                  <strong>{id === 1 ? score1 : score2}</strong>
                </div>
              </div>
              <div className="score-adjustments">
                {/* Plus buttons */}
                <div className="score-adjustments__row">
                  {[1, 2, 3].map((v) => (
                    <Button
                      disabled={disabled}
                      key={v}
                      variant="outline"
                      className="score-button"
                      size="sm"
                      onClick={() => onAdjustScore(id as 1 | 2, v)}
                    >
                      +{v}
                    </Button>
                  ))}
                </div>
                {/* Minus buttons */}
                <div className="score-adjustments__row">
                  {[-1, -2, -3].map((v) => (
                    <Button
                      disabled={disabled}
                      key={v}
                      variant="outline"
                      className="score-button"
                      size="sm"
                      onClick={() => onAdjustScore(id as 1 | 2, v)}
                    >
                      {v}
                    </Button>
                  ))}
                </div>
              </div>
            </div>

            {/* Shido */}
            <div className="fighter-penalties">
              <span className="fighter-penalties__label">{t("match.penalty")}</span>
              <div className="fighter-penalties__buttons">
                {[
                  { value: 0, label: t("match.none") },
                  { value: 1, label: "C1" },
                  { value: 2, label: "C2" },
                  { value: 3, label: "C3" },
                  { value: 4, label: "HC" },
                  { value: 5, label: "H" },
                ].map(({ value, label }) => (
                  <Button
                    disabled={disabled}
                    key={value}
                    variant={value === (id === 1 ? shido1 : shido2) ? "default" : "outline"}
                    size="sm"
                    onClick={() => onSetShido(id as 1 | 2, value)}
                  >
                    {label}
                  </Button>
                ))}
              </div>
            </div>
          </section>
        );
      })}
    </div>
  );
}
