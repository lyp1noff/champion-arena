import { useEffect, useState, useRef } from "react";
import { Bracket, BracketMatches, BracketType, Category, Participant } from "@/lib/interfaces";
import { BracketView } from "@/components/bracket-view";
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
import SettingsDialog from "./components/SettingsDialog";
import CreateBracketDialog from "./components/CreateBracketDialog";
import CreateCategoryDialog from "./components/CreateCategoryDialog";
import UnsavedChangesDialog from "./components/UnsavedChangesDialog";
import {
  regenerateBracket,
  reorderParticipants,
  createBracket,
  getCategories,
  createCategory,
  moveParticipant,
} from "@/lib/api/brackets";
import DeleteBracketDialog from "./components/DeleteBracketDialog";

interface Props {
  tournamentId: number;
  brackets: Bracket[];
  selectedBracket: Bracket | null;
  bracketMatches?: BracketMatches;
  loading: boolean;
  onSelectBracket: (bracket: Bracket) => Promise<void>;
  onSaveBracket: (updated: {
    id: number;
    type: BracketType;
    start_time: string;
    tatami: number;
    group_id: number;
    category_id?: number;
  }) => Promise<void>;
  onBracketsUpdate: () => void;
}

export default function ManageTournamentPage({
  tournamentId,
  brackets,
  selectedBracket,
  bracketMatches,
  loading,
  onSelectBracket,
  onSaveBracket,
  onBracketsUpdate,
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
  const originalParticipantsRef = useRef<Participant[]>([]);
  const [settingsForm, setSettingsForm] = useState({
    type: "single_elimination" as BracketType,
    start_time: "",
    tatami: "" as number | "",
    group_id: 1,
    category_id: 0,
  });
  const [newBracket, setNewBracket] = useState({
    category_id: "",
    group_id: 1,
    type: "single_elimination" as BracketType,
    start_time: "",
    tatami: "",
  });
  const [newCategory, setNewCategory] = useState({
    name: "",
    age: "",
    gender: "male",
  });
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [bracketToDelete, setBracketToDelete] = useState<Bracket | null>(null);
  const [transferTargetId, setTransferTargetId] = useState<number | null>(null);

  // --- Effects ---
  useEffect(() => {
    if (selectedBracket) {
      setParticipants(selectedBracket.participants);
      originalParticipantsRef.current = selectedBracket.participants;
      setSettingsForm({
        type: selectedBracket.type || "single_elimination",
        start_time: selectedBracket.start_time || "",
        tatami: selectedBracket.tatami ?? "",
        group_id: selectedBracket.group_id ?? 1,
        category_id: categories.find((c) => c.name === selectedBracket.category)?.id ?? 0,
      });
    } else {
      setParticipants([]);
      originalParticipantsRef.current = [];
      setSettingsForm({
        type: "single_elimination",
        start_time: "",
        tatami: "",
        group_id: 1,
        category_id: 0,
      });
    }
  }, [selectedBracket, categories]);

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
    if (participants.length !== originalParticipantsRef.current.length) return true;
    for (let i = 0; i < participants.length; i++) {
      if (participants[i].athlete_id !== originalParticipantsRef.current[i].athlete_id) return true;
      if (participants[i].seed !== originalParticipantsRef.current[i].seed) return true;
    }
    return false;
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
      const participantUpdates = participants.map((p, idx) => ({ athlete_id: p.athlete_id, new_seed: idx + 1 }));
      await reorderParticipants(selectedBracket.id, participantUpdates);
      await regenerateBracket(selectedBracket.id);
      toast.success("Bracket updated and regenerated successfully");
      onBracketsUpdate();
      originalParticipantsRef.current = [...participants];
    } catch {
      toast.error("Failed to save bracket");
    }
  };

  // --- Dialog Handlers ---
  const handleSettingsSave = async () => {
    if (!selectedBracket) return;
    if (settingsForm.tatami === "" || !settingsForm.category_id) {
      toast.error("Tatami and category are required.");
      return;
    }
    await onSaveBracket({
      id: selectedBracket.id,
      type: settingsForm.type,
      start_time: settingsForm.start_time,
      tatami: Number(settingsForm.tatami),
      group_id: settingsForm.group_id,
      category_id: settingsForm.category_id,
    });
    setShowSettings(false);
    onBracketsUpdate();
  };

  const handleCreateBracket = async () => {
    if (!newBracket.category_id || !newBracket.tatami) return;
    try {
      await createBracket({
        tournament_id: tournamentId,
        category_id: Number(newBracket.category_id),
        group_id: newBracket.group_id,
        type: newBracket.type,
        start_time: newBracket.start_time || undefined,
        tatami: Number(newBracket.tatami),
      });
      toast.success("Bracket created successfully");
      setShowCreateBracket(false);
      setNewBracket({ category_id: "", group_id: 1, type: "single_elimination", start_time: "", tatami: "" });
      onBracketsUpdate();
    } catch {
      toast.error("Failed to create bracket");
    }
  };

  const handleCreateCategory = async () => {
    if (!newCategory.name || !newCategory.age) return;
    try {
      await createCategory({
        name: newCategory.name,
        age: Number(newCategory.age),
        gender: newCategory.gender,
      });
      toast.success("Category created successfully");
      setShowCreateCategory(false);
      setNewCategory({ name: "", age: "", gender: "male" });
      loadCategories();
    } catch {
      toast.error("Failed to create category");
    }
  };

  const handleRegenerate = async () => {
    if (!selectedBracket) return;
    try {
      await regenerateBracket(selectedBracket.id);
      toast.success("Bracket regenerated successfully");
      onBracketsUpdate();
    } catch {
      toast.error("Failed to regenerate bracket");
    }
  };

  // --- Context Menu Handlers ---
  const handleDeleteBracket = (bracket: Bracket) => {
    setBracketToDelete(bracket);
    setShowDeleteDialog(true);
  };

  const handleEditBracket = async (bracket: Bracket) => {
    if (!selectedBracket || selectedBracket.id !== bracket.id) {
      await onSelectBracket(bracket);
    }
    setShowSettings(true);
  };

  const handleConfirmDelete = () => {
    // TODO: Implement API call for delete/transfer
    setShowDeleteDialog(false);
    setBracketToDelete(null);
    setTransferTargetId(null);
    toast.success("Bracket deleted (not really, just UI)");
  };
  const handleCancelDelete = () => {
    setShowDeleteDialog(false);
    setBracketToDelete(null);
    setTransferTargetId(null);
  };

  // --- Move Participant Handler ---
  const handleMoveParticipant = async (participant: Participant, targetBracketId: number) => {
    if (!selectedBracket) return;
    try {
      await moveParticipant(participant.athlete_id, selectedBracket.id, targetBracketId);
      const targetBracket = brackets.find((b) => b.id === targetBracketId);
      toast.success(
        <>
          Participant moved to:
          <br />
          {targetBracket?.display_name || targetBracket?.category || targetBracketId.toString()}
        </>,
      );
      // Update local participants state for immediate feedback
      setParticipants((prev) => prev.filter((p) => p.athlete_id !== participant.athlete_id));
      await onBracketsUpdate();
    } catch (e: unknown) {
      if (e instanceof Error) {
        toast.error(e.message || "Failed to move participant");
      } else {
        toast.error("Failed to move participant");
      }
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
        <div className="flex-1 flex flex-col gap-4 h-full overflow-auto">
          {selectedBracket ? (
            <>
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">{selectedBracket.display_name || selectedBracket.category}</h2>
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
                      <BracketView loading={loading} matches={bracketMatches ?? []} bracket={selectedBracket} />
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
      <SettingsDialog
        open={showSettings}
        onClose={() => setShowSettings(false)}
        settingsForm={settingsForm}
        setSettingsForm={setSettingsForm}
        onSave={handleSettingsSave}
        categories={categories}
        selectedBracket={selectedBracket}
      />
      <CreateBracketDialog
        open={showCreateBracket}
        onClose={() => setShowCreateBracket(false)}
        newBracket={newBracket}
        setNewBracket={setNewBracket}
        onCreate={handleCreateBracket}
        categories={categories}
        onShowCreateCategory={() => setShowCreateCategory(true)}
      />
      <CreateCategoryDialog
        open={showCreateCategory}
        onClose={() => setShowCreateCategory(false)}
        newCategory={newCategory}
        setNewCategory={setNewCategory}
        onCreate={handleCreateCategory}
      />
      <UnsavedChangesDialog open={showUnsavedDialog} onDiscard={confirmSwitch} onCancel={cancelSwitch} />
      <DeleteBracketDialog
        open={showDeleteDialog}
        onClose={handleCancelDelete}
        bracketToDelete={bracketToDelete}
        brackets={brackets}
        transferTargetId={transferTargetId}
        setTransferTargetId={setTransferTargetId}
        onConfirm={handleConfirmDelete}
      />
    </DndContext>
  );
}
