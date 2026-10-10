import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import { TIMER_STATUS, TimerStatus } from "@/store/tatami";

interface MatchControlsProps {
  timerStatus: TimerStatus;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
}

export function MatchControls({ timerStatus, onStart, onPause, onResume }: MatchControlsProps) {
  const { t } = useI18n();
  return (
    <div className="match-primary-control">
      {timerStatus === TIMER_STATUS.RUNNING && <Button onClick={onPause}>{t("match.pause")}</Button>}
      {timerStatus === TIMER_STATUS.IDLE && <Button onClick={onStart}>{t("match.start")}</Button>}
      {timerStatus === TIMER_STATUS.PAUSED && <Button onClick={onResume}>{t("match.resume")}</Button>}
    </div>
  );
}
