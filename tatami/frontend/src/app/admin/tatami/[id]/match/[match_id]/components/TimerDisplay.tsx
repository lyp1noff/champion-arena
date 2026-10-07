interface TimerDisplayProps {
  remaining: number;
  durationMs: number;
}

export function TimerDisplay({ remaining, durationMs }: TimerDisplayProps) {
  const { t } = useI18n();
  const format = (ms: number) => {
    const clamped = Math.max(0, ms);
    const s = Math.floor(clamped / 1000);
    const m = Math.floor(s / 60);
    const remS = s % 60;
    const remMS = Math.floor((clamped % 1000) / 10);
    return `${String(m).padStart(2, "0")}:${String(remS).padStart(2, "0")}.${String(remMS).padStart(2, "0")}`;
  };

  return (
    <div className="match-timer">
      <div className="match-timer__value">{format(remaining)}</div>
      <div className="match-timer__duration">
        {t("match.duration", {
          duration: `${Math.floor(durationMs / 60000)}:${String(Math.floor((durationMs % 60000) / 1000)).padStart(2, "0")}`,
        })}
      </div>
    </div>
  );
}
import { useI18n } from "@/lib/i18n";
