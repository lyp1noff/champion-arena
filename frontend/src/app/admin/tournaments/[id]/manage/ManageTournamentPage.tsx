import { useEffect, useState } from "react";
import { Bracket, BracketMatches, BracketType, Category, Participant } from "@/lib/interfaces";
import { BracketView } from "@/components/bracket/bracket-view";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Plus, RefreshCw, Save } from "lucide-react";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
} from "@dnd-kit/core";
import { arrayMove } from "@dnd-kit/sortable";
import { toast } from "sonner";
import BracketCard from "./components/BracketCard";
import ParticipantsList from "./components/ParticipantsList";
import CreateCategoryDialog from "./components/CreateCategoryDialog";
import UnsavedChangesDialog from "./components/UnsavedChangesDialog";
import {
  regenerateBracket,
  reorderParticipants,
  createBracket,
  getCategories,
  createCategory,
  moveParticipant,
  deleteBracket,
} from "@/lib/api/brackets";
import DeleteBracketDialog from "./components/DeleteBracketDialog";
import DeleteParticipantDialog from "./components/DeleteParticipantDialog";
import { deleteParticipant } from "@/lib/api/tournaments";
import {
  CreateBracketSchema,
  defaultBracketValues,
} from "@/app/admin/tournaments/[id]/manage/components/bracketSchema";
import BracketFormDialog from "@/app/admin/tournaments/[id]/manage/components/BracketFormDialog";
import { WebSocketProvider } from "@/components/websocket-provider";
import { getBracketDisplayName } from "@/lib/utils";

interface Props {
  tournamentId: number;
  brackets: Bracket[];
  selectedBracket: Bracket | null;
  bracketMatches?: BracketMatches;
  loading: boolean;
  onSelectBracket: (bracket: Bracket | null) => Promise<void>;
  onSaveBracket: (updated: {
    id: number;
    type: BracketType;
    start_time: string;
    tatami: number;
    group_id: number;
    category_id?: string;
  }) => Promise<void>;
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
      start_time: selectedBracket.start_time ?? defaultBracketValues.start_time,
      day: selectedBracket.day ?? defaultBracketValues.day,
      tatami: selectedBracket.tatami ?? defaultBracketValues.tatami,
    });
  }, [categories, selectedBracket]);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const categoriesData = await getCategories();
      setCategories(categoriesData);
    } catch (error) {
      console.error("Failed to load categories:", error);
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

  // --- Unsaved Changes ---
  const hasPendingChanges = () => {
    if (!selectedBracket) return false;
    return JSON.stringify(participants) !== JSON.stringify(selectedBracket.participants);
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
        start_time: data.start_time,
        day: data.day,
        tatami: data.tatami,
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
          <ScrollArea className="flex-1 max-h-full overflow-auto">
            <div className="space-y-3 p-1">
              {brackets.map((bracket) => (
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
            </div>
          </ScrollArea>
        </div>

        {/* Middle Column - Bracket Preview */}

        <WebSocketProvider tournamentId={tournamentId.toString()}>
          <div className="flex-1 flex flex-col gap-4 h-full overflow-auto">
            {selectedBracket ? (
              <>
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold pl-3">
                    {getBracketDisplayName(selectedBracket.category, selectedBracket.group_id)}
                  </h2>
                  <div className="flex gap-2">
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
                        <BracketView matches={bracketMatches ?? []} bracketType={selectedBracket.type} />
                      </div>
                      <ScrollBar orientation="horizontal" />
                      <ScrollBar orientation="vertical" />
                    </ScrollArea>
                  </CardContent>
                </Card>
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
