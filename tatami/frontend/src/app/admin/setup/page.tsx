"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  getCurrentTournament,
  getOutboxStatus,
  getTatamis,
  getTournaments,
  setCurrentTournament,
  syncTournament,
} from "@/lib/api";
import { Tournament } from "@/lib/interfaces";

export default function SetupPage() {
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  const [availableTatamis, setAvailableTatamis] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [selectedTournament, setSelectedTournament] = useState<number | null>(null);
  const [outboxStatus, setOutboxStatus] = useState<{
    total: number;
    pending: number;
    failed: number;
    succeeded: number;
  } | null>(null);

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
        const [tournamentData, currentTournament] = await Promise.all([
          getTournaments(),
          getCurrentTournament(),
        ]);
        setTournaments(tournamentData);
        setSelectedTournament(currentTournament.current_tournament_id);

        if (currentTournament.current_tournament_id) {
          await fetchAvailableTatamis(currentTournament.current_tournament_id);
        }
      } catch (error) {
        console.error("Error bootstrapping setup page:", error);
      } finally {
        setLoading(false);
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
      alert(result.message ?? `Tournament sync ${result.status}`);
    } catch (error) {
      console.error("Error syncing tournament:", error);
      alert(error instanceof Error ? error.message : "Error syncing tournament");
    } finally {
      setSyncing(false);
    }
  };

  const handleTatamiSelect = (tatamiId: number) => {
    window.open(`/admin/tatami/${tatamiId}`, "_blank");
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Tournament Setup</h1>

          <div className="space-y-6">
            {outboxStatus && (
              <div>
                <h2 className="text-xl font-bold text-gray-900 mb-4">Outbox Summary</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-gray-900">{outboxStatus.total}</p>
                    <p className="text-sm text-gray-600">Total</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-2xl font-bold text-green-800">{outboxStatus.succeeded}</p>
                    <p className="text-sm text-green-700">Succeeded</p>
                  </div>
                  <div className="p-4 bg-yellow-50 rounded-lg">
                    <p className="text-2xl font-bold text-yellow-800">{outboxStatus.pending}</p>
                    <p className="text-sm text-yellow-700">Pending</p>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <p className="text-2xl font-bold text-red-800">{outboxStatus.failed}</p>
                    <p className="text-sm text-red-700">Failed</p>
                  </div>
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Select Tournament</label>
              <Select
                value={selectedTournament?.toString() || undefined}
                onValueChange={(value) => handleTournamentSelect(parseInt(value, 10))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose a tournament" />
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
                  {syncing ? "Syncing..." : "Bootstrap Selected Tournament"}
                </Button>
              )}
              <Button asChild variant="outline" className="px-4">
                <Link href="/admin/brackets">Open Bracket Admin</Link>
              </Button>
            </div>

            {selectedTournament && (
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-blue-800">Selected: {tournaments.find((t) => t.id === selectedTournament)?.name}</p>
              </div>
            )}

            {selectedTournament && availableTatamis.length > 0 && (
              <div>
                <h2 className="text-lg font-semibold mb-4">Available Tatamis</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {availableTatamis.map((tatamiId) => (
                    <Button
                      key={tatamiId}
                      onClick={() => handleTatamiSelect(tatamiId)}
                      className="h-20 text-lg font-semibold"
                    >
                      Tatami {tatamiId}
                    </Button>
                  ))}
                </div>
              </div>
            )}

            {selectedTournament && availableTatamis.length === 0 && !loading && (
              <div className="bg-yellow-50 p-4 rounded-lg">
                <p className="text-yellow-800">No tatamis assigned to this tournament. Bootstrap the tournament first.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
