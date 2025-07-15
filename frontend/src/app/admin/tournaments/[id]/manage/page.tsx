"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getTournamentBracketsById } from "@/lib/api/tournaments";
import { getBracketMatchesById, updateBracket } from "@/lib/api/brackets";
import { toast } from "sonner";
import { Bracket, BracketMatches, BracketType } from "@/lib/interfaces";
import ManageTournamentPage from "./ManageTournamentPage";
import { formatTimeToISO } from "@/lib/utils";

export default function Page() {
  const { id } = useParams();
  const tournamentId = Number(id);

  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [bracketMatches, setBracketMatches] = useState<BracketMatches>();
  const [selectedBracket, setSelectedBracket] = useState<Bracket | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getTournamentBracketsById(tournamentId)
      .then(setBrackets)
      .catch((err) => {
        console.error(err);
        toast.error("Failed to fetch brackets");
      });
  }, [tournamentId]);

  const fetchMatches = async (bracketId: number) => {
    setLoading(true);
    try {
      const matches = await getBracketMatchesById(bracketId);
      setBracketMatches(matches);
    } catch {
      toast.error("Failed to fetch matches");
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (bracket: Bracket) => {
    setSelectedBracket(bracket);
    await fetchMatches(bracket.id);
  };

  const handleSave = async (updated: { id: number; type: BracketType; start_time: string; tatami: number }) => {
    setLoading(true);
    try {
      const formatted = {
        ...updated,
        start_time: formatTimeToISO(updated.start_time),
      };
      await updateBracket(updated.id, formatted);
      toast.success("Bracket saved");

      const refreshed = await getTournamentBracketsById(tournamentId);
      setBrackets(refreshed);
      const newSelected = refreshed.find((b) => b.id === updated.id);
      if (newSelected) setSelectedBracket(newSelected);
      await fetchMatches(updated.id);
    } catch {
      toast.error("Failed to save bracket");
    } finally {
      setLoading(false);
    }
  };

  const handleBracketsUpdate = async () => {
    try {
      const refreshed = await getTournamentBracketsById(tournamentId);
      setBrackets(refreshed);
      if (selectedBracket) {
        const newSelected = refreshed.find((b) => b.id === selectedBracket.id);
        if (newSelected) {
          setSelectedBracket(newSelected);
          await fetchMatches(newSelected.id);
        }
      }
    } catch (error) {
      console.error("Failed to refresh brackets:", error);
      toast.error("Failed to refresh brackets");
    }
  };

  return (
    <ManageTournamentPage
      tournamentId={tournamentId}
      brackets={brackets}
      selectedBracket={selectedBracket}
      bracketMatches={bracketMatches}
      loading={loading}
      onSelectBracket={handleSelect}
      onSaveBracket={handleSave}
      onBracketsUpdate={handleBracketsUpdate}
    />
  );
}
