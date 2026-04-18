"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { BracketParticipantControls } from "@/components/admin/bracket-participant-controls";
import { BracketParticipantTable } from "@/components/admin/bracket-participant-table";
import { SearchablePicker } from "@/components/admin/searchable-picker";
import {
  addBracketParticipant,
  deleteBracketParticipant,
  getBracketParticipants,
  getBrackets,
  getCurrentTournament,
  getExternalAthletes,
  moveBracketParticipant,
  updateBracketParticipantSeed,
} from "@/lib/api";
import { Athlete, Bracket, BracketParticipant } from "@/lib/interfaces";

export function BracketAdmin() {
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [participants, setParticipants] = useState<BracketParticipant[]>([]);
  const [externalAthletes, setExternalAthletes] = useState<Athlete[]>([]);
  const [selectedTournament, setSelectedTournament] = useState<number | null>(null);
  const [selectedBracket, setSelectedBracket] = useState<number | null>(null);
  const [selectedAthleteExternalId, setSelectedAthleteExternalId] = useState<number | null>(null);
  const [participantSeed, setParticipantSeed] = useState("");
  const [moveTargets, setMoveTargets] = useState<Record<number, string>>({});
  const [seedEdits, setSeedEdits] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [participantActionLoading, setParticipantActionLoading] = useState(false);

  const fetchParticipants = useCallback(async (bracketId: number | null) => {
    if (!bracketId) {
      setParticipants([]);
      return;
    }

    const data = await getBracketParticipants(bracketId);
    setParticipants(data);
    setSeedEdits(Object.fromEntries(data.map((participant) => [participant.id, String(participant.seed)])));
  }, []);

  const fetchBrackets = useCallback(async (tournamentId: number, preferredBracketId: number | null = null) => {
    const data = await getBrackets(String(tournamentId));
    setBrackets(data);

    const resolvedBracketId =
      preferredBracketId && data.some((bracket) => bracket.external_id === preferredBracketId)
        ? preferredBracketId
        : data[0]?.external_id ?? null;

    setSelectedBracket(resolvedBracketId);
    await fetchParticipants(resolvedBracketId);
  }, [fetchParticipants]);

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
      return;
    }

    fetchParticipants(selectedBracket).catch((error) => {
      console.error("Error fetching participants:", error);
      setParticipants([]);
    });
  }, [fetchParticipants, selectedBracket]);

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
      alert(error instanceof Error ? error.message : "Failed to add participant");
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
      alert(error instanceof Error ? error.message : "Failed to remove participant");
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
      alert(error instanceof Error ? error.message : "Failed to move participant");
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
      alert("Seed must be a positive number");
      return;
    }

    try {
      setParticipantActionLoading(true);
      await updateBracketParticipantSeed(selectedBracket, participantId, seedValue);
      await fetchBrackets(selectedTournament, selectedBracket);
    } catch (error) {
      console.error("Error updating seed:", error);
      alert(error instanceof Error ? error.message : "Failed to update seed");
    } finally {
      setParticipantActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border bg-white p-6">
        <p className="text-sm text-gray-600">Loading bracket admin...</p>
      </div>
    );
  }

  if (!selectedTournament) {
    return (
      <div className="rounded-lg border bg-white p-6">
        <h1 className="text-2xl font-bold text-gray-900">Bracket Admin</h1>
        <p className="mt-2 text-sm text-gray-600">Select and bootstrap a tournament first in setup.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-lg border bg-white p-6">
        <h1 className="text-2xl font-bold text-gray-900">Bracket Admin</h1>
        <p className="mt-2 text-sm text-gray-600">
          Add athletes from the full arena list, remove them from one bracket only, or move them between brackets.
          Every change regenerates the affected brackets locally.
        </p>
      </div>

      <div className="space-y-3 rounded-lg border bg-white p-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Selected Bracket</label>
          <SearchablePicker
            options={brackets.map((bracket) => ({
              value: bracket.external_id.toString(),
              label: bracket.display_name || bracket.category,
              keywords: `${bracket.display_name || bracket.category} ${bracket.category}`,
            }))}
            value={selectedBracket?.toString()}
            placeholder="Choose a bracket"
            searchPlaceholder="Search brackets..."
            emptyText="No brackets found."
            onChange={(value) => setSelectedBracket(parseInt(value, 10))}
          />
        </div>
      </div>

      {selectedBracket ? (
        <>
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
            onMove={handleMoveParticipant}
            onRemove={handleRemoveParticipant}
          />
        </>
      ) : (
        <div className="rounded-lg border bg-white p-6">
          <p className="text-sm text-gray-600">No brackets available for the selected tournament.</p>
        </div>
      )}
    </div>
  );
}
