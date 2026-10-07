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

interface TimeSettingProps {
  timeSettingInput: { minutes: number; seconds: number };
  showTimeSettingDialog: boolean;
  onTimeSettingInputChange: (field: "minutes" | "seconds", value: number) => void;
  onShowTimeSettingDialogChange: (show: boolean) => void;
  onSaveTimeSetting: () => void;
}

export function TimeSetting({
  timeSettingInput,
  showTimeSettingDialog,
  onTimeSettingInputChange,
  onShowTimeSettingDialogChange,
  onSaveTimeSetting,
}: TimeSettingProps) {
  const { t } = useI18n();
  return (
    <div className="border rounded-lg p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">{t("match.timeSetting")}</h3>
        <Dialog open={showTimeSettingDialog} onOpenChange={onShowTimeSettingDialogChange}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              {t("match.setTime")}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("match.settingTitle")}</DialogTitle>
              <DialogDescription>{t("match.settingDescription")}</DialogDescription>
            </DialogHeader>
            <div className="flex items-center gap-2 justify-center py-4">
              <input
                type="number"
                min="0"
                max="59"
                value={timeSettingInput.minutes}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0;
                  onTimeSettingInputChange("minutes", value);
                }}
                className="w-20 px-3 py-2 border rounded text-center text-lg"
                placeholder={t("match.minutesShort")}
              />
              <span className="text-lg font-bold">:</span>
              <input
                type="number"
                min="0"
                max="59"
                value={timeSettingInput.seconds}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 0;
                  onTimeSettingInputChange("seconds", value);
                }}
                className="w-20 px-3 py-2 border rounded text-center text-lg"
                placeholder={t("match.secondsShort")}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => onShowTimeSettingDialogChange(false)}>
                {t("common.cancel")}
              </Button>
              <Button onClick={onSaveTimeSetting}>{t("match.saveTime")}</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
