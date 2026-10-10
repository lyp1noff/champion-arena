import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useI18n } from "@/lib/i18n";
import { TIMER_STATUS, TimerStatus } from "@/store/tatami";

interface TimeAdjustmentProps {
  timerStatus: TimerStatus;
  timeAdjustInput: { minutes: number; seconds: number; milliseconds: number };
  showTimeAdjustDialog: boolean;
  onTimeAdjustInputChange: (field: "minutes" | "seconds" | "milliseconds", value: number) => void;
  onShowTimeAdjustDialogChange: (show: boolean) => void;
  onSaveTimeAdjustment: () => void;
}

export function TimeAdjustment({
  timerStatus,
  timeAdjustInput,
  showTimeAdjustDialog,
  onTimeAdjustInputChange,
  onShowTimeAdjustDialogChange,
  onSaveTimeAdjustment,
}: TimeAdjustmentProps) {
  const { t } = useI18n();
  if (timerStatus !== TIMER_STATUS.PAUSED) return null;

  return (
    <div className="border rounded-lg p-4 border-yellow-500 bg-yellow-50">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-yellow-800">{t("match.adjustment")}</h3>
        <Dialog open={showTimeAdjustDialog} onOpenChange={onShowTimeAdjustDialogChange}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm" className="text-yellow-800 border-yellow-500">
              {t("match.adjust")}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("match.adjustTitle")}</DialogTitle>
              <DialogDescription>{t("match.adjustDescription")}</DialogDescription>
            </DialogHeader>
            <div className="flex items-center gap-2 justify-center py-4">
              <input
                type="number"
                min="0"
                max="59"
                value={timeAdjustInput.minutes}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0;
                  onTimeAdjustInputChange("minutes", value);
                }}
                className="w-20 px-3 py-2 border rounded text-center text-lg"
                placeholder={t("match.minutesShort")}
              />
              <span className="text-lg font-bold">:</span>
              <input
                type="number"
                min="0"
                max="59"
                value={timeAdjustInput.seconds}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0;
                  onTimeAdjustInputChange("seconds", value);
                }}
                className="w-20 px-3 py-2 border rounded text-center text-lg"
                placeholder={t("match.secondsShort")}
              />
              <span className="text-lg font-bold">.</span>
              <input
                type="number"
                min="0"
                max="99"
                value={timeAdjustInput.milliseconds}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0;
                  onTimeAdjustInputChange("milliseconds", value);
                }}
                className="w-20 px-3 py-2 border rounded text-center text-lg"
                placeholder={t("match.centisecondsShort")}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => onShowTimeAdjustDialogChange(false)}>
                {t("common.cancel")}
              </Button>
              <Button onClick={onSaveTimeAdjustment}>{t("match.saveTime")}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
