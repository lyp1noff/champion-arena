"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { BracketParticipantControls } from "@/components/admin/bracket-participant-controls";
import { BracketParticipantTable } from "@/components/admin/bracket-participant-table";
import { BracketResults } from "@/components/admin/bracket-results";
import { SearchablePicker } from "@/components/admin/searchable-picker";
import {
  addBracketParticipant,
  correctMatchResult,
  deleteBracketParticipant,
  getBracketParticipants,
  getBrackets,
  getCurrentTournament,
  getExternalAthletes,
  getMatches,
  moveBracketParticipant,
  updateBracketParticipantSeed,
} from "@/lib/api";
import { Athlete, Bracket, BracketMatch, BracketParticipant } from "@/lib/interfaces";
import { useI18n } from "@/lib/i18n";

export function BracketAdmin() {
  const { t } = useI18n();
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [participants, setParticipants] = useState<BracketParticipant[]>([]);
  const [matches, setMatches] = useState<BracketMatch[]>([]);
  const [externalAthletes, setExternalAthletes] = useState<Athlete[]>([]);
  const [selectedTournament, setSelectedTournament] = useState<number | null>(null);
  const [selectedBracket, setSelectedBracket] = useState<number | null>(null);
  const [selectedAthleteExternalId, setSelectedAthleteExternalId] = useState<number | null>(null);
  const [participantSeed, setParticipantSeed] = useState("");
  const [moveTargets, setMoveTargets] = useState<Record<number, string>>({});
  const [seedEdits, setSeedEdits] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [participantActionLoading, setParticipantActionLoading] = useState(false);
  const [resultActionLoading, setResultActionLoading] = useState(false);

  const fetchParticipants = useCallback(async (bracketId: number | null) => {
    if (!bracketId) {
      setParticipants([]);
      return;
    }

    const data = await getBracketParticipants(bracketId);
    setParticipants(data);
    setSeedEdits(Object.fromEntries(data.map((participant) => [participant.id, String(participant.seed)])));
  }, []);

  const fetchMatches = useCallback(async (bracketId: number | null) => {
    if (!bracketId) {
      setMatches([]);
      return;
    }
    setMatches(await getMatches(String(bracketId)));
  }, []);

  const fetchBrackets = useCallback(async (tournamentId: number, preferredBracketId: number | null = null) => {
    const data = await getBrackets(String(tournamentId));
    setBrackets(data);

    const resolvedBracketId =
      preferredBracketId && data.some((bracket) => bracket.external_id === preferredBracketId)
        ? preferredBracketId
        : data[0]?.external_id ?? null;

    setSelectedBracket(resolvedBracketId);
    await Promise.all([fetchParticipants(resolvedBracketId), fetchMatches(resolvedBracketId)]);
  }, [fetchMatches, fetchParticipants]);

  useEffect(() => {
    const bootstrapPage = async () => {
      try {
        setLoading(true);
        const [currentTournament, athleteData] = await Promise.all([getCurrentTournament(), getExternalAthletes()]);
        setExternalAthletes(athleteData);
        setSelectedTournament(currentTournament.current_tournament_id);

        if (currentTournament.current_tournament_id) {
          await fetchBrackets(currentTournament.current_tournament_id);
        }
      } catch (error) {
        console.error("Error bootstrapping bracket admin:", error);
      } finally {
        setLoading(false);
      }
    };

    bootstrapPage();
  }, [fetchBrackets]);

  useEffect(() => {
    if (!selectedBracket) {
      setParticipants([]);
      setMatches([]);
      return;
    }

    Promise.all([fetchParticipants(selectedBracket), fetchMatches(selectedBracket)]).catch((error) => {
      console.error("Error fetching bracket data:", error);
      setParticipants([]);
      setMatches([]);
    });
  }, [fetchMatches, fetchParticipants, selectedBracket]);

  const addableAthletes = useMemo(() => {
    return externalAthletes.filter((athlete) => {
      const externalId = athlete.external_id ?? athlete.id;
      return !participants.some((participant) => participant.athlete?.external_id === externalId);
    });
  }, [externalAthletes, participants]);

  const handleAddParticipant = async () => {
    if (!selectedTournament || !selectedBracket || !selectedAthleteExternalId) {
      return;
    }

    try {
      setParticipantActionLoading(true);
      await addBracketParticipant(
        selectedBracket,
        selectedAthleteExternalId,
        participantSeed.trim() ? parseInt(participantSeed, 10) : undefined,
      );
      setParticipantSeed("");
      await fetchBrackets(selectedTournament, selectedBracket);
    } catch (error) {
      console.error("Error adding participant:", error);
      alert(error instanceof Error ? error.message : t("brackets.addError"));
    } finally {
      setParticipantActionLoading(false);
    }
  };

  const handleRemoveParticipant = async (participantId: number) => {
    if (!selectedTournament || !selectedBracket) {
      return;
    }

    try {
      setParticipantActionLoading(true);
      await deleteBracketParticipant(selectedBracket, participantId);
      await fetchBrackets(selectedTournament, selectedBracket);
    } catch (error) {
      console.error("Error removing participant:", error);
      alert(error instanceof Error ? error.message : t("brackets.removeError"));
    } finally {
      setParticipantActionLoading(false);
    }
  };

  const handleMoveParticipant = async (participantId: number) => {
    if (!selectedTournament) {
      return;
    }

    const targetBracketId = moveTargets[participantId];
    if (!targetBracketId) {
      return;
    }

    try {
      setParticipantActionLoading(true);
      await moveBracketParticipant(participantId, parseInt(targetBracketId, 10));
      setMoveTargets((current) => ({ ...current, [participantId]: "" }));
      await fetchBrackets(selectedTournament, selectedBracket);
    } catch (error) {
      console.error("Error moving participant:", error);
      alert(error instanceof Error ? error.message : t("brackets.moveError"));
    } finally {
      setParticipantActionLoading(false);
    }
  };

  const handleSeedSave = async (participantId: number) => {
    if (!selectedTournament || !selectedBracket) {
      return;
    }

    const seedValue = parseInt(seedEdits[participantId] ?? "", 10);
    if (!Number.isFinite(seedValue) || seedValue < 1) {
      alert(t("brackets.seedPositive"));
      return;
    }

    try {
      setParticipantActionLoading(true);
      await updateBracketParticipantSeed(selectedBracket, participantId, seedValue);
      await fetchBrackets(selectedTournament, selectedBracket);
    } catch (error) {
      console.error("Error updating seed:", error);
      alert(error instanceof Error ? error.message : t("brackets.seedError"));
    } finally {
      setParticipantActionLoading(false);
    }
  };

  const handleSeedReorder = async (participantId: number, targetSeed: number) => {
    if (!selectedTournament || !selectedBracket) {
      return;
    }

    try {
      setParticipantActionLoading(true);
      await updateBracketParticipantSeed(selectedBracket, participantId, targetSeed);
      await fetchBrackets(selectedTournament, selectedBracket);
    } catch (error) {
      console.error("Error reordering participant:", error);
      alert(error instanceof Error ? error.message : t("brackets.reorderError"));
    } finally {
      setParticipantActionLoading(false);
    }
  };

  const handleCorrectResult = async (
    bracketMatch: BracketMatch,
    score1: number,
    score2: number,
    winnerId: number,
  ) => {
    if (!selectedBracket) return;
    try {
      setResultActionLoading(true);
      await correctMatchResult(bracketMatch.match.external_id, score1, score2, winnerId);
      await fetchMatches(selectedBracket);
    } finally {
      setResultActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border bg-white p-6">
        <p className="text-sm text-gray-600">{t("brackets.loading")}</p>
      </div>
    );
  }

  if (!selectedTournament) {
    return (
      <div className="rounded-lg border bg-white p-6">
        <h1 className="text-2xl font-bold text-gray-900">{t("brackets.title")}</h1>
        <p className="mt-2 text-sm text-gray-600">{t("brackets.noTournament")}</p>
      </div>
    );
  }

  return (
    <div className="bracket-admin">
      <div className="admin-card admin-card--intro">
        <div>
          <h1>{t("brackets.title")}</h1>
          <p>{t("brackets.description")}</p>
        </div>
        <span className="admin-count">{t("brackets.athleteCount", { count: participants.length })}</span>
      </div>

      <div className="admin-card bracket-selector">
        <div className="admin-field">
          <label>{t("brackets.selected")}</label>
          <SearchablePicker
            options={brackets.map((bracket) => ({
              value: bracket.external_id.toString(),
              label: bracket.display_name || bracket.category,
              keywords: `${bracket.display_name || bracket.category} ${bracket.category}`,
            }))}
            value={selectedBracket?.toString()}
            placeholder={t("brackets.choose")}
            searchPlaceholder={t("brackets.search")}
            emptyText={t("brackets.none")}
            onChange={(value) => setSelectedBracket(parseInt(value, 10))}
          />
        </div>
      </div>

      {selectedBracket ? (
        <>
          <BracketResults matches={matches} loading={resultActionLoading} onCorrect={handleCorrectResult} />
          <BracketParticipantControls
            athletes={addableAthletes}
            selectedAthleteExternalId={selectedAthleteExternalId}
            participantSeed={participantSeed}
            loading={participantActionLoading}
            onSelectAthlete={setSelectedAthleteExternalId}
            onSeedChange={setParticipantSeed}
            onAdd={handleAddParticipant}
          />
          <BracketParticipantTable
            participants={participants}
            brackets={brackets}
            selectedBracketId={selectedBracket}
            loading={participantActionLoading}
            moveTargets={moveTargets}
            seedEdits={seedEdits}
            onMoveTargetChange={(participantId, value) =>
              setMoveTargets((current) => ({ ...current, [participantId]: value }))
            }
            onSeedEditChange={(participantId, value) =>
              setSeedEdits((current) => ({ ...current, [participantId]: value }))
            }
            onSeedSave={handleSeedSave}
            onReorder={handleSeedReorder}
            onMove={handleMoveParticipant}
            onRemove={handleRemoveParticipant}
          />
        </>
      ) : (
        <div className="rounded-lg border bg-white p-6">
          <p className="text-sm text-gray-600">{t("brackets.noAvailable")}</p>
        </div>
      )}
    </div>
  );
}
