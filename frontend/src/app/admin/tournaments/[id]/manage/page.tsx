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
    getTournamentBracketsById(tournamentId, false)
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

  const refreshBracketsAndSelect = async (bracketId: number | null) => {
    const refreshed = await getTournamentBracketsById(tournamentId, false);
    setBrackets(refreshed);

    if (bracketId !== null) {
      const updated = refreshed.find((b) => b.id === bracketId) ?? null;
      setSelectedBracket(updated);
      if (updated) {
        await fetchMatches(updated.id);
      } else {
        setBracketMatches(undefined);
      }
    } else {
      setSelectedBracket(null);
      setBracketMatches(undefined);
    }
  };

  const handleSelect = async (bracket: Bracket | null) => {
    await refreshBracketsAndSelect(bracket?.id ?? null);
  };

  const handleSave = async (updated: {
    id: number;
    type: BracketType;
    start_time: string;
    tatami: number;
    group_id: number;
    category_id?: string;
  }) => {
    setLoading(true);
    try {
      const formatted = {
        ...updated,
        start_time: formatTimeToISO(updated.start_time),
        category_id: updated.category_id ? parseInt(updated.category_id) : undefined,
      };
      await updateBracket(updated.id, formatted);
      toast.success("Bracket saved");
      await refreshBracketsAndSelect(updated.id);
    } catch {
      toast.error("Failed to save bracket");
    } finally {
      setLoading(false);
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
    />
  );
}
