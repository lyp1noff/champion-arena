import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import BracketFormDialog from "@/app/admin/tournaments/[id]/manage/components/BracketFormDialog";
import {
  CreateBracketSchema,
  defaultBracketValues,
} from "@/app/admin/tournaments/[id]/manage/components/bracketSchema";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import { Plus, RefreshCw, Save, Settings2 } from "lucide-react";
import { toast } from "sonner";

import { BracketView, type Placement } from "@/components/bracket/bracket-view";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { WebSocketProvider } from "@/components/websocket-provider";

import {
  createBracket,
  createCategory,
  deleteBracket,
  getCategories,
  moveParticipant,
  regenerateBracket,
  reorderParticipants,
} from "@/lib/api/brackets";
import { finishMatch, startMatch, updateMatchScores } from "@/lib/api/matches";
import { deleteParticipant } from "@/lib/api/tournaments";
import { Bracket, BracketMatches, BracketType, Category, Participant } from "@/lib/interfaces";
import { getBracketDisplayName } from "@/lib/utils";

import BracketCard from "./components/BracketCard";
import CreateCategoryDialog from "./components/CreateCategoryDialog";
import DeleteBracketDialog from "./components/DeleteBracketDialog";
import DeleteParticipantDialog from "./components/DeleteParticipantDialog";
import ParticipantsList from "./components/ParticipantsList";
import UnsavedChangesDialog from "./components/UnsavedChangesDialog";

interface Props {
  tournamentId: number;
  brackets: Bracket[];
  selectedBracket: Bracket | null;
  bracketMatches?: BracketMatches;
  loading: boolean;
  onSelectBracket: (bracket: Bracket | null) => Promise<void>;
  onSaveBracket: (updated: { id: number; type: BracketType; group_id: number; category_id?: string }) => Promise<void>;
}

export default function ManageTournamentPage({
  tournamentId,
  brackets,
  selectedBracket,
  bracketMatches,
  loading,
  onSelectBracket,
  onSaveBracket,
}: Props) {
  // --- State ---
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [showCreateBracket, setShowCreateBracket] = useState(false);
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showUnsavedDialog, setShowUnsavedDialog] = useState(false);
  const [pendingBracketSwitch, setPendingBracketSwitch] = useState<Bracket | null>(null);
  const [draggedParticipant, setDraggedParticipant] = useState<{ participant: Participant; bracketId: number } | null>(
    null,
  );
  const [settingsForm, setSettingsForm] = useState<Partial<CreateBracketSchema>>({
    ...defaultBracketValues,
  });
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [bracketToDelete, setBracketToDelete] = useState<Bracket | null>(null);
  const [bracketToTransfer, setBracketToTransfer] = useState<Bracket | null>(null);
  const [showDeleteParticipantDialog, setShowDeleteParticipantDialog] = useState(false);
  const [participantToDelete, setParticipantToDelete] = useState<Participant | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showMatchControl, setShowMatchControl] = useState(false);
  const [showBracketId, setShowBracketId] = useState(false);
  const [scoreDrafts, setScoreDrafts] = useState<Record<string, { s1: string; s2: string }>>({});
  const [matchActionId, setMatchActionId] = useState<string | null>(null);
  const [bracketsSearch, setBracketsSearch] = useState("");
  const selectedBracketRef = useRef<Bracket | null>(null);
  const refreshInFlightRef = useRef(false);
  const refreshQueuedRef = useRef(false);

  // --- Effects ---
  useEffect(() => {
    if (!selectedBracket) {
      setParticipants([]);
      setSettingsForm({
        ...defaultBracketValues,
      });
      return;
    }

    const matchedCategory = categories.find((c) => c.name === selectedBracket.category);

    setParticipants(selectedBracket.participants);

    setSettingsForm({
      category_id: matchedCategory?.id?.toString() ?? defaultBracketValues.category_id,
      group_id: selectedBracket.group_id ?? defaultBracketValues.group_id,
      type: selectedBracket.type ?? defaultBracketValues.type,
    });
  }, [categories, selectedBracket]);

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    if (!bracketMatches) return;
    const next: Record<string, { s1: string; s2: string }> = {};
    for (const bm of bracketMatches) {
      next[bm.match.id] = {
        s1: bm.match.score_athlete1?.toString() ?? "0",
        s2: bm.match.score_athlete2?.toString() ?? "0",
      };
    }
    setScoreDrafts(next);
  }, [bracketMatches]);

  useEffect(() => {
    selectedBracketRef.current = selectedBracket;
  }, [selectedBracket]);

  const loadCategories = async () => {
    try {
      const categoriesData = await getCategories();
      setCategories(categoriesData);
    } catch (error) {
      console.error("Failed to load categories:", error);
    }
  };

  const filteredBrackets = useMemo(() => {
    const q = bracketsSearch.trim().toLowerCase();
    if (!q) return brackets;

    return brackets.filter((bracket) => {
      const displayName = getBracketDisplayName(bracket.category, bracket.group_id).toLowerCase();
      if (displayName.includes(q)) return true;

      return bracket.participants.some((participant) => {
        const firstName = participant.first_name.toLowerCase();
        const lastName = participant.last_name.toLowerCase();
        const coaches = participant.coaches_last_name.join(" ").toLowerCase();
        return firstName.includes(q) || lastName.includes(q) || coaches.includes(q);
      });
    });
  }, [brackets, bracketsSearch]);

  const selectedBracketPlacements = useMemo<Placement[]>(() => {
    if (!selectedBracket) return [];
    const placements: Placement[] = [];
    if (selectedBracket.place_1) placements.push({ place: 1, athlete: selectedBracket.place_1 });
    if (selectedBracket.place_2) placements.push({ place: 2, athlete: selectedBracket.place_2 });
    if (selectedBracket.place_3_a) placements.push({ place: 3, athlete: selectedBracket.place_3_a });
    if (selectedBracket.place_3_b) placements.push({ place: 3, athlete: selectedBracket.place_3_b });
    return placements;
  }, [selectedBracket]);

  const hasPendingChanges = useCallback(() => {
    if (!selectedBracket) return false;
    return JSON.stringify(participants) !== JSON.stringify(selectedBracket.participants);
  }, [participants, selectedBracket]);

  const refreshSelectedFromWebSocket = useCallback(() => {
    const run = async () => {
      const current = selectedBracketRef.current;
      if (!current || hasPendingChanges()) return;

      if (refreshInFlightRef.current) {
        refreshQueuedRef.current = true;
        return;
      }

      refreshInFlightRef.current = true;
      try {
        await onSelectBracket(current);
      } finally {
        refreshInFlightRef.current = false;
        if (refreshQueuedRef.current) {
          refreshQueuedRef.current = false;
          void run();
        }
      }
    };

    void run();
  }, [hasPendingChanges, onSelectBracket]);

  const refreshSelected = async () => {
    if (!selectedBracket) return;
    await onSelectBracket(selectedBracket);
  };

  const handleStartMatch = async (matchId: string) => {
    setMatchActionId(matchId);
    try {
      await startMatch(matchId);
      await refreshSelected();
      toast.success("Match started");
    } catch (error) {
      console.error(error);
      toast.error("Failed to start match");
    } finally {
      setMatchActionId(null);
    }
  };

  const handleSaveScores = async (matchId: string) => {
    const draft = scoreDrafts[matchId];
    if (!draft) return;
    setMatchActionId(matchId);
    try {
      await updateMatchScores(matchId, {
        score_athlete1: Number(draft.s1),
        score_athlete2: Number(draft.s2),
      });
      await refreshSelected();
      toast.success("Scores updated");
    } catch (error) {
      console.error(error);
      toast.error("Failed to update scores");
    } finally {
      setMatchActionId(null);
    }
  };

  const handleFinishMatch = async (matchId: string, winnerId: number | undefined) => {
    const draft = scoreDrafts[matchId];
    if (!draft || !winnerId) return;
    setMatchActionId(matchId);
    try {
      await finishMatch(matchId, {
        score_athlete1: Number(draft.s1),
        score_athlete2: Number(draft.s2),
        winner_id: winnerId,
      });
      await refreshSelected();
      toast.success("Match finished");
    } catch (error) {
      console.error(error);
      toast.error("Failed to finish match");
    } finally {
      setMatchActionId(null);
    }
  };

  // --- Drag and Drop ---
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
  );

  const handleDragStart = (event: DragStartEvent) => {
    const [bracketId, seed] = event.active.id.toString().split("-");
    const bracket = brackets.find((b) => b.id === Number(bracketId));
    const participant = bracket?.participants.find((p) => p.seed === Number(seed));
    if (participant && bracket) {
      setDraggedParticipant({ participant, bracketId: Number(bracketId) });
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setDraggedParticipant(null);
    const { active, over } = event;
    if (!over) return;
    const [activeBracketId, activeSeed] = active.id.toString().split("-");
    const [overBracketId, overSeed] = over.id.toString().split("-");
    if (!selectedBracket || selectedBracket.id !== Number(activeBracketId)) return;
    if (activeBracketId === overBracketId) {
      const oldIndex = participants.findIndex((p) => p.seed === Number(activeSeed));
      const newIndex = participants.findIndex((p) => p.seed === Number(overSeed));
      if (oldIndex !== newIndex) {
        const reordered = arrayMove(participants, oldIndex, newIndex).map((p, idx) => ({ ...p, seed: idx + 1 }));
        setParticipants(reordered);
      }
    }
  };

  const handleBracketSelect = async (bracket: Bracket) => {
    if (hasPendingChanges()) {
      setPendingBracketSwitch(bracket);
      setShowUnsavedDialog(true);
    } else {
      await onSelectBracket(bracket);
    }
  };

  const confirmSwitch = async () => {
    setShowUnsavedDialog(false);
    if (pendingBracketSwitch) {
      await onSelectBracket(pendingBracketSwitch);
      setPendingBracketSwitch(null);
    }
  };
  const cancelSwitch = () => {
    setShowUnsavedDialog(false);
    setPendingBracketSwitch(null);
  };

  // --- Save/Regenerate ---
  const handleSave = async () => {
    if (!selectedBracket) {
      toast.error("No bracket selected.");
      return;
    }
    try {
      const participantUpdates = participants.map((p, idx) => ({ participant_id: p.id, new_seed: idx + 1 }));
      const participantsData = { bracket_id: selectedBracket.id, participant_updates: participantUpdates };
      await reorderParticipants(participantsData);
      await regenerateBracket(selectedBracket.id);
      toast.success("Bracket updated and regenerated successfully");
      await onSelectBracket(selectedBracket);
    } catch {
      toast.error("Failed to save bracket");
    }
  };

  // --- Dialog Handlers ---
  const handleCreateBracket = async (data: CreateBracketSchema) => {
    try {
      const bracketData = {
        tournament_id: tournamentId,
        category_id: Number(data.category_id),
        group_id: data.group_id,
        type: data.type,
      };
      const newBracketObj = await createBracket(bracketData);
      toast.success("Bracket created successfully");
      await onSelectBracket(newBracketObj);
    } catch {
      toast.error("Failed to create bracket");
    }
  };

  const handleRegenerate = async () => {
    if (!selectedBracket) return;
    try {
      await regenerateBracket(selectedBracket.id);
      toast.success("Bracket regenerated successfully");
      await onSelectBracket(selectedBracket);
    } catch {
      toast.error("Failed to regenerate bracket");
    }
  };

  // --- Edit Bracket Handler ---
  const handleEditBracket = async (bracket: Bracket) => {
    if (!selectedBracket || selectedBracket.id !== bracket.id) {
      await onSelectBracket(bracket);
    }
    setShowSettings(true);
  };

  // --- Delete Bracket Handler ---
  const handleDeleteBracket = (bracket: Bracket) => {
    setBracketToDelete(bracket);
    setShowDeleteDialog(true);
  };

  const handleBracketConfirmDelete = async () => {
    if (!bracketToDelete) {
      toast.error("Bracket not found");
      return;
    }

    setShowDeleteDialog(false);

    try {
      await deleteBracket(bracketToDelete.id, bracketToTransfer ? { target_bracket_id: bracketToTransfer.id } : {});
      toast.success("Bracket deleted");

      await onSelectBracket(bracketToTransfer ?? null);
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to delete bracket");
    } finally {
      setBracketToDelete(null);
      setBracketToTransfer(null);
    }
  };

  const handleCancelDelete = () => {
    setShowDeleteDialog(false);
    setBracketToDelete(null);
    setBracketToTransfer(null);
  };

  // --- Move Participant Handler ---
  const handleMoveParticipant = async (participant: Participant, targetBracketId: number) => {
    if (!selectedBracket) return;
    try {
      const moveData = {
        participant_id: participant.id,
        from_bracket_id: selectedBracket.id,
        to_bracket_id: targetBracketId,
      };
      await moveParticipant(moveData);
      const targetBracket = brackets.find((b) => b.id === targetBracketId);
      toast.success(
        <>
          Participant moved to:
          <br />
          {getBracketDisplayName(targetBracket?.category, targetBracket?.group_id)}
        </>,
      );
      await onSelectBracket(selectedBracket);
    } catch (e: unknown) {
      if (e instanceof Error) {
        toast.error(e.message);
      } else {
        toast.error("Failed to move participant");
      }
    }
  };

  // --- Delete Participant Handler ---
  const handleDeleteParticipant = (participant: Participant) => {
    setParticipantToDelete(participant);
    setShowDeleteParticipantDialog(true);
  };

  const handleCompetitorConfirmDelete = async () => {
    if (!participantToDelete) return;
    setIsDeleting(true);
    try {
      await deleteParticipant(participantToDelete.id);
      toast.success("Participant deleted successfully");
      setShowDeleteParticipantDialog(false);
      await onSelectBracket(selectedBracket);
    } catch {
      toast.error("Failed to delete participant");
    } finally {
      setIsDeleting(false);
    }
  };

  // --- Render ---
  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 p-4" style={{ height: "calc(100dvh - 65px)" }}>
        {/* Left Column - Brackets List */}
        <div className="min-w-80 max-w-80 flex flex-col gap-4 h-full">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Brackets</h2>
            <Button size="sm" onClick={() => setShowCreateBracket(true)}>
              <Plus className="h-4 w-4 mr-1" />
              New Bracket
            </Button>
          </div>
          <Input
            value={bracketsSearch}
            onChange={(e) => setBracketsSearch(e.target.value)}
            placeholder="Search bracket / participant / coach"
          />
          <ScrollArea className="flex-1 max-h-full overflow-auto">
            <div className="space-y-3 p-1">
              {filteredBrackets.map((bracket) => (
                <BracketCard
                  key={bracket.id}
                  bracket={bracket}
                  isSelected={selectedBracket?.id === bracket.id}
                  onSelect={() => handleBracketSelect(bracket)}
                  participants={bracket.participants}
                  onDeleteBracket={handleDeleteBracket}
                  onEditBracket={handleEditBracket}
                />
              ))}
              {filteredBrackets.length === 0 && (
                <div className="text-sm text-muted-foreground px-2 py-1">No brackets found.</div>
              )}
            </div>
          </ScrollArea>
        </div>

        {/* Middle Column - Bracket Preview */}

        <WebSocketProvider tournamentId={tournamentId.toString()} onAnyUpdate={refreshSelectedFromWebSocket}>
          <div className="flex-1 flex flex-col gap-4 h-full overflow-auto">
            {selectedBracket ? (
              <>
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold pl-3 flex items-center gap-2">
                    {getBracketDisplayName(selectedBracket.category, selectedBracket.group_id)}
                    {showBracketId && (
                      <span className="text-sm font-normal text-muted-foreground">#{selectedBracket.id}</span>
                    )}
                  </h2>
                  <div className="flex gap-2">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="outline" size="icon" aria-label="Manage view options">
                          <Settings2 className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>Admin view</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuCheckboxItem
                          checked={showMatchControl}
                          onCheckedChange={(checked) => setShowMatchControl(Boolean(checked))}
                        >
                          Match Control
                        </DropdownMenuCheckboxItem>
                        <DropdownMenuCheckboxItem
                          checked={showBracketId}
                          onCheckedChange={(checked) => setShowBracketId(Boolean(checked))}
                        >
                          Show ID
                        </DropdownMenuCheckboxItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                    <Button variant="outline" onClick={handleRegenerate} disabled={loading}>
                      <RefreshCw className="h-4 w-4 mr-1" />
                      Regenerate
                    </Button>
                    <Button onClick={handleSave} disabled={loading}>
                      <Save className="h-4 w-4 mr-1" />
                      Save & Regenerate
                    </Button>
                  </div>
                </div>
                <Card className="flex-1 h-full flex flex-col overflow-auto">
                  <CardContent className="flex-1 p-0 h-full">
                    <ScrollArea className="h-full w-full">
                      <div className="p-6 h-full w-full">
                        <BracketView
                          matches={bracketMatches ?? []}
                          bracketType={selectedBracket.type}
                          placements={selectedBracketPlacements}
                        />
                      </div>
                      <ScrollBar orientation="horizontal" />
                      <ScrollBar orientation="vertical" />
                    </ScrollArea>
                  </CardContent>
                </Card>
                {showMatchControl && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Matches Control</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3 max-h-72 overflow-auto">
                        {(bracketMatches ?? []).map((bm) => {
                          const draft = scoreDrafts[bm.match.id] ?? { s1: "0", s2: "0" };
                          const athlete1 = bm.match.athlete1;
                          const athlete2 = bm.match.athlete2;
                          const disabled = matchActionId === bm.match.id;
                          return (
                            <div key={bm.id} className="rounded-md border p-3">
                              <div className="text-xs text-muted-foreground mb-2">
                                R{bm.round_number} • #{bm.position} • {bm.match.status}
                              </div>
                              <div className="grid grid-cols-[1fr_90px_90px_auto] gap-2 items-center">
                                <div className="text-sm truncate">
                                  {athlete1 ? `${athlete1.last_name} ${athlete1.first_name}` : "TBD"} vs{" "}
                                  {athlete2 ? `${athlete2.last_name} ${athlete2.first_name}` : "TBD"}
                                </div>
                                <Input
                                  type="number"
                                  value={draft.s1}
                                  onChange={(e) =>
                                    setScoreDrafts((prev) => ({
                                      ...prev,
                                      [bm.match.id]: { ...draft, s1: e.target.value },
                                    }))
                                  }
                                />
                                <Input
                                  type="number"
                                  value={draft.s2}
                                  onChange={(e) =>
                                    setScoreDrafts((prev) => ({
                                      ...prev,
                                      [bm.match.id]: { ...draft, s2: e.target.value },
                                    }))
                                  }
                                />
                                <div className="flex gap-1">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    disabled={disabled || bm.match.status !== "not_started"}
                                    onClick={() => handleStartMatch(bm.match.id)}
                                  >
                                    Start
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    disabled={disabled || bm.match.status !== "started"}
                                    onClick={() => handleSaveScores(bm.match.id)}
                                  >
                                    Save
                                  </Button>
                                  <Button
                                    size="sm"
                                    disabled={disabled || bm.match.status !== "started" || !athlete1}
                                    onClick={() => handleFinishMatch(bm.match.id, athlete1?.id)}
                                  >
                                    Finish A
                                  </Button>
                                  <Button
                                    size="sm"
                                    disabled={disabled || bm.match.status !== "started" || !athlete2}
                                    onClick={() => handleFinishMatch(bm.match.id, athlete2?.id)}
                                  >
                                    Finish B
                                  </Button>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-muted-foreground">
                Select a bracket to view details
              </div>
            )}
          </div>
        </WebSocketProvider>

        {/* Right Column - Options & Participants */}
        <div className="min-w-80 max-w-80 flex flex-col h-full gap-4">
          {selectedBracket ? (
            <>
              <Button variant="outline" className="w-full" onClick={() => setShowSettings(true)}>
                Settings
              </Button>
              <Card className="flex-1 max-h-full overflow-auto">
                <CardHeader>
                  <CardTitle>
                    Participants
                    {hasPendingChanges() && (
                      <span style={{ color: "red", fontSize: 12, marginLeft: 8 }}>(Unsaved changes)</span>
                    )}
                  </CardTitle>
                  <div className="text-sm text-muted-foreground">Drag to reorder or move between brackets</div>
                </CardHeader>
                <CardContent className="max-h-full p-0">
                  <ParticipantsList
                    participants={participants}
                    bracketId={selectedBracket.id}
                    eligibleBrackets={brackets}
                    onMoveParticipant={handleMoveParticipant}
                    onDeleteParticipant={handleDeleteParticipant}
                  />
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              Select a bracket to manage
            </div>
          )}
        </div>
      </div>
      <DragOverlay>
        {draggedParticipant && (
          <ParticipantsList participants={[draggedParticipant.participant]} bracketId={draggedParticipant.bracketId} />
        )}
      </DragOverlay>
      {/* Dialogs */}
      <BracketFormDialog
        open={showCreateBracket}
        onClose={() => setShowCreateBracket(false)}
        onSubmit={handleCreateBracket}
        categories={categories}
        loadCategories={() => loadCategories()}
      />
      <BracketFormDialog
        open={showSettings}
        onClose={() => setShowSettings(false)}
        mode="edit"
        categories={categories}
        initialValues={settingsForm}
        onSubmit={async (data) => {
          if (!selectedBracket) return;
          await onSaveBracket({ id: selectedBracket.id, ...data });
        }}
        loadCategories={() => loadCategories()}
      />
      <CreateCategoryDialog
        open={showCreateCategory}
        onClose={() => setShowCreateCategory(false)}
        onCreate={async (data) => {
          await createCategory(data);
          toast.success("Category created");
          setCategories(await getCategories());
        }}
      />
      <UnsavedChangesDialog open={showUnsavedDialog} onDiscard={confirmSwitch} onCancel={cancelSwitch} />
      <DeleteBracketDialog
        open={showDeleteDialog}
        onClose={handleCancelDelete}
        bracketToDelete={bracketToDelete}
        brackets={brackets}
        bracketToTransfer={bracketToTransfer}
        setBracketToTransfer={setBracketToTransfer}
        onConfirm={handleBracketConfirmDelete}
      />
      <DeleteParticipantDialog
        open={showDeleteParticipantDialog}
        onClose={() => setShowDeleteParticipantDialog(false)}
        participantToDelete={participantToDelete}
        isLoading={isDeleting}
        onConfirm={handleCompetitorConfirmDelete}
      />
    </DndContext>
  );
}
