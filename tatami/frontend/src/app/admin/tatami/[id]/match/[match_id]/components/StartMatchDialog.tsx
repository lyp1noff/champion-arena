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
import { ExternalMatch } from "@/lib/interfaces";
import { useState } from "react";
import { useI18n } from "@/lib/i18n";

interface StartMatchDialogProps {
  currentMatch: ExternalMatch | null;
  status: string;
  onStartMatch: () => void;
}

export function StartMatchDialog({ currentMatch, status, onStartMatch }: StartMatchDialogProps) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);

  const handleOpenChange = (newOpen: boolean) => {
    setOpen(newOpen);
  };

  const handleStart = () => {
    onStartMatch();
    setOpen(false);
  };

  const athlete1Name = currentMatch?.athlete1
    ? `${currentMatch.athlete1.last_name} ${currentMatch.athlete1.first_name} (${currentMatch.athlete1.coaches_last_name})`
    : t("match.fighter", { id: 1 });

  const athlete2Name = currentMatch?.athlete2
    ? `${currentMatch.athlete2.last_name} ${currentMatch.athlete2.first_name} (${currentMatch.athlete2.coaches_last_name})`
    : t("match.fighter", { id: 2 });

  const isDisabled = status === "running" || currentMatch?.status === "started";

  return (
    <div className="border rounded-lg p-4 border-green-500 bg-green-50">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-green-800">{t("match.start")}</h3>
        <Dialog open={open} onOpenChange={handleOpenChange}>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm" className="text-green-800 border-green-500" disabled={isDisabled}>
              {t("match.start")}
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>{t("match.start")}</DialogTitle>
              <DialogDescription>{t("match.startDescription")}</DialogDescription>
            </DialogHeader>

            <div className="space-y-4 py-4">
              {/* Match Info */}
              <div className="space-y-3">
                <div className="text-center">
                  <div className="text-lg font-semibold text-gray-800">VS</div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-center">
                  <div className="p-3 border rounded-lg bg-red-50">
                    <div className="text-lg font-bold text-red-600">{athlete1Name}</div>
                  </div>
                  <div className="p-3 border rounded-lg bg-blue-50">
                    <div className="text-lg font-bold text-blue-600">{athlete2Name}</div>
                  </div>
                </div>

                {/* Match Details */}
                <div className="text-center space-y-1">
                  <div className="text-sm text-gray-600">
                    <strong>{t("match.id")}:</strong> {currentMatch?.external_id}
                  </div>
                  <div className="text-sm text-gray-600">
                    <strong>{t("common.status")}:</strong>{" "}
                    {currentMatch?.status === "not_started" ? t("match.ready") : currentMatch?.status}
                  </div>
                </div>
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>
                {t("common.cancel")}
              </Button>
              <Button onClick={handleStart} className="bg-green-600 hover:bg-green-700" disabled={isDisabled}>
                {t("match.start")}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
