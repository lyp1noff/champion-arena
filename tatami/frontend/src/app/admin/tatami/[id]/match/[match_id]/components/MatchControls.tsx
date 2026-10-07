import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";

interface MatchControlsProps {
  status: string;
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
}

export function MatchControls({ status, onStart, onPause, onResume }: MatchControlsProps) {
  const { t } = useI18n();
  return (
    <div className="match-primary-control">
      {status === "running" && <Button onClick={onPause}>{t("match.pause")}</Button>}
      {status === "idle" && <Button onClick={onStart}>{t("match.start")}</Button>}
      {status === "paused" && <Button onClick={onResume}>{t("match.resume")}</Button>}
    </div>
  );
}
