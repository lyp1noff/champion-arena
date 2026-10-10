"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  getCurrentTournament,
  getExternalTournaments,
  getLocalTournaments,
  getOutboxStatus,
  getTatamis,
  rebootstrapTournament,
  setCurrentTournament,
  syncTournament,
} from "@/lib/api";
import { Tournament } from "@/lib/interfaces";
import { useI18n } from "@/lib/i18n";

function mergeTournaments(local: Tournament[], external: Tournament[]): Tournament[] {
  const byId = new Map(local.map((tournament) => [tournament.id, tournament]));
  for (const tournament of external) {
    byId.set(tournament.id, tournament);
  }
  return Array.from(byId.values());
}

export default function SetupPage() {
  const { t } = useI18n();
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [availableTatamis, setAvailableTatamis] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [rebootstrapping, setRebootstrapping] = useState(false);
  const [selectedTournament, setSelectedTournament] = useState<number | null>(null);
  const [rebootstrapDialogOpen, setRebootstrapDialogOpen] = useState(false);
  const [rebootstrapStep, setRebootstrapStep] = useState<1 | 2>(1);
  const [outboxStatus, setOutboxStatus] = useState<{
    total: number;
    pending: number;
    failed: number;
    succeeded: number;
  } | null>(null);

  const getOperationStatus = (status: string) =>
    ["success", "error", "ok"].includes(status) ? t(`setup.status.${status}`) : status;

  const fetchOutboxStatus = async () => {
    try {
      const data = await getOutboxStatus();
      setOutboxStatus(data);
    } catch (error) {
      console.error("Error fetching outbox status:", error);
    }
  };

  const fetchAvailableTatamis = async (tournamentId: number) => {
    try {
      const data = await getTatamis(tournamentId);
      setAvailableTatamis(data.tatamis);
    } catch (error) {
      console.error("Error fetching available tatamis:", error);
    }
  };

  useEffect(() => {
    fetchOutboxStatus();
  }, []);

  useEffect(() => {
    const interval = setInterval(fetchOutboxStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const bootstrapPage = async () => {
      try {
        setLoading(true);
        const [localTournaments, currentTournament] = await Promise.all([
          getLocalTournaments(),
          getCurrentTournament(),
        ]);
        setTournaments(localTournaments);
        setSelectedTournament(currentTournament.current_tournament_id);

        if (currentTournament.current_tournament_id) {
          await fetchAvailableTatamis(currentTournament.current_tournament_id);
        }
      } catch (error) {
        console.error("Error bootstrapping setup page:", error);
      } finally {
        setLoading(false);
      }

      // Arena is optional at runtime. Locally bootstrapped tournaments are
      // already usable; when Arena is reachable, extend the picker with
      // tournaments that can still be bootstrapped.
      try {
        const externalTournaments = await getExternalTournaments();
        setTournaments((localTournaments) => mergeTournaments(localTournaments, externalTournaments));
      } catch (error) {
        console.info("Arena is unavailable; using local tournaments only", error);
      }
    };

    bootstrapPage();
  }, []);

  const handleTournamentSelect = async (tournamentId: number) => {
    try {
      await setCurrentTournament(tournamentId);
      setSelectedTournament(tournamentId);
      await fetchAvailableTatamis(tournamentId);
    } catch (error) {
      console.error("Error saving tournament selection:", error);
    }
  };

  const runTournamentSync = async () => {
    if (!selectedTournament) return;

    try {
      setSyncing(true);
      const result = await syncTournament(selectedTournament);
      await Promise.all([fetchAvailableTatamis(selectedTournament), fetchOutboxStatus()]);
      alert(t("setup.syncResult", { status: getOperationStatus(result.status) }));
    } catch (error) {
      console.error("Error syncing tournament:", error);
      alert(t("setup.syncError"));
    } finally {
      setSyncing(false);
    }
  };

  const handleTatamiSelect = (tatamiId: number) => {
    window.open(`/admin/tatami/${tatamiId}`, "_blank");
  };

  const handleRebootstrapOpenChange = (open: boolean) => {
    setRebootstrapDialogOpen(open);
    if (!open) {
      setRebootstrapStep(1);
    }
  };

  const runTournamentRebootstrap = async () => {
    if (!selectedTournament) return;

    try {
      setRebootstrapping(true);
      const result = await rebootstrapTournament(selectedTournament);
      await Promise.all([fetchAvailableTatamis(selectedTournament), fetchOutboxStatus()]);
      handleRebootstrapOpenChange(false);
      alert(t("setup.rebootstrapResult", { status: getOperationStatus(result.status) }));
    } catch (error) {
      console.error("Error rebootstraping tournament:", error);
      alert(t("setup.rebootstrapError"));
    } finally {
      setRebootstrapping(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">{t("setup.title")}</h1>

          <div className="space-y-6">
            {outboxStatus && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4">{t("setup.outbox")}</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-gray-900">{outboxStatus.total}</p>
                    <p className="text-sm text-gray-600">{t("setup.total")}</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-800">{outboxStatus.succeeded}</p>
                    <p className="text-sm text-green-700">{t("setup.succeeded")}</p>
                  </div>
                  <div className="p-4 bg-yellow-50 rounded-lg">
                    <p className="text-2xl font-bold text-yellow-800">{outboxStatus.pending}</p>
                    <p className="text-sm text-yellow-700">{t("setup.pending")}</p>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <p className="text-2xl font-bold text-red-800">{outboxStatus.failed}</p>
                    <p className="text-sm text-red-700">{t("setup.failed")}</p>
                  </div>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t("setup.selectTournament")}</label>
              <Select
                value={selectedTournament?.toString() || undefined}
                onValueChange={(value) => handleTournamentSelect(parseInt(value, 10))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={t("setup.chooseTournament")} />
                </SelectTrigger>
                <SelectContent>
                  {tournaments.map((tournament) => (
                    <SelectItem key={tournament.id} value={tournament.id.toString()}>
                      {tournament.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-wrap gap-4">
              {selectedTournament && (
                <Button onClick={runTournamentSync} disabled={syncing} variant="outline" className="px-4">
                  {syncing ? t("setup.syncing") : t("setup.bootstrap")}
                </Button>
              )}
              {selectedTournament && (
                <Button
                  onClick={() => handleRebootstrapOpenChange(true)}
                  disabled={rebootstrapping}
                  variant="destructive"
                  className="px-4"
                >
                  {t("setup.rebootstrap")}
                </Button>
              )}
              <Button asChild variant="outline" className="px-4">
                <a href="/admin/brackets">{t("setup.openBrackets")}</a>
              </Button>
            </div>

            {selectedTournament && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-blue-800">{t("setup.selected", { name: tournaments.find((item) => item.id === selectedTournament)?.name ?? "" })}</p>
              </div>
            )}

            {selectedTournament && availableTatamis.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold mb-4">{t("setup.availableTatamis")}</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {availableTatamis.map((tatamiId) => (
                    <Button
                      key={tatamiId}
                      onClick={() => handleTatamiSelect(tatamiId)}
                      className="h-20 text-lg font-semibold"
                    >
                      {t("common.tatami", { id: tatamiId })}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {selectedTournament && availableTatamis.length === 0 && !loading && (
              <div className="bg-yellow-50 p-4 rounded-lg">
                <p className="text-yellow-800">{t("setup.noTatamis")}</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <Dialog open={rebootstrapDialogOpen} onOpenChange={handleRebootstrapOpenChange}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {rebootstrapStep === 1 ? t("setup.rebootstrapTitle") : t("setup.rebootstrapFinalTitle")}
            </DialogTitle>
            <DialogDescription className="text-left">
              {rebootstrapStep === 1
                ? t("setup.rebootstrapDescription")
                : t("setup.rebootstrapFinalDescription")}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => handleRebootstrapOpenChange(false)} disabled={rebootstrapping}>
              {t("common.cancel")}
            </Button>
            {rebootstrapStep === 1 ? (
              <Button variant="destructive" onClick={() => setRebootstrapStep(2)} disabled={rebootstrapping}>
                {t("common.confirm")}
              </Button>
            ) : (
              <Button variant="destructive" onClick={runTournamentRebootstrap} disabled={rebootstrapping}>
                {rebootstrapping ? t("setup.rebootstrapRunning") : t("setup.rebootstrapFinalConfirm")}
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
