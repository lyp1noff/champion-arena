"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Dispatch, ReactNode, SetStateAction } from "react";

import { useParams } from "next/navigation";

import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  closestCenter,
  useDraggable,
  useDroppable,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import { SortableContext, arrayMove, useSortable, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Pencil, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import {
  getTournamentBracketsById,
  getTournamentTimetableById,
  replaceTournamentTimetable,
} from "@/lib/api/tournaments";
import { Bracket, TimetableEntry, TimetableEntryType } from "@/lib/interfaces";
import { getBracketDisplayName } from "@/lib/utils";

type ColumnKey = string;
type ActiveMeta = { kind: "entry"; id: number; day: number; tatami: number } | { kind: "pool"; bracketId: number };

function buildColumnKey(day: number, tatami: number) {
  return `${day}-${tatami}`;
}

function getBracketTypeLabel(type: string) {
  return type === "round_robin" ? "Round Robin" : "Single Elim";
}

function parsePositiveInt(value: string, fallback = 1): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.max(1, Math.floor(parsed));
}

const SHOW_OVERLAY_FOR_POOL = true;

export default function TimetablePage() {
  const { id } = useParams();
  const tournamentId = Number(id);

  const [entries, setEntries] = useState<TimetableEntry[]>([]);
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [activeMeta, setActiveMeta] = useState<ActiveMeta | null>(null);
  const [poolPreview, setPoolPreview] = useState<{
    day: number;
    tatami: number;
    insertIndex: number;
    bracketId: number;
  } | null>(null);
  const tempIdRef = useRef(-1);
  const [selectedDay, setSelectedDay] = useState<number>(1);
  const [dayCount, setDayCount] = useState(1);
  const [tatamiCount, setTatamiCount] = useState(1);
  const [openDialog, setOpenDialog] = useState(false);
  const [editEntry, setEditEntry] = useState<TimetableEntry | null>(null);
  const [editPayload, setEditPayload] = useState({ day: 1, tatami: 1, title: "", notes: "" });
  const [createPayload, setCreatePayload] = useState({
    entry_type: "bracket" as TimetableEntryType,
    day: 1,
    tatami: 1,
    start_time: "09:00",
    end_time: "09:00",
    order_index: 1,
    title: "",
    notes: "",
    bracket_id: null as number | null,
  });

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
  );

  useEffect(() => {
    if (!tournamentId) return;
    Promise.all([getTournamentTimetableById(tournamentId), getTournamentBracketsById(tournamentId)])
      .then(([timetable, bracketsData]) => {
        setEntries(timetable);
        setBrackets(bracketsData);
        const days = [...new Set(timetable.map((entry) => entry.day))];
        if (days.length) {
          setSelectedDay(days.sort()[0]);
        }
        const maxDay = Math.max(1, ...timetable.map((entry) => entry.day));
        const maxTatami = Math.max(1, ...timetable.map((entry) => entry.tatami));
        setDayCount(maxDay);
        setTatamiCount(maxTatami);
      })
      .catch(() => toast.error("Failed to load timetable"));
  }, [tournamentId]);

  const bracketMap = useMemo(() => {
    const map = new Map<number, Bracket>();
    for (const bracket of brackets) {
      map.set(bracket.id, bracket);
    }
    return map;
  }, [brackets]);

  const unscheduledBrackets = useMemo(() => {
    const scheduled = new Set(entries.filter((e) => e.entry_type === "bracket").map((e) => e.bracket_id));
    return brackets.filter((b) => !scheduled.has(b.id));
  }, [entries, brackets]);
  const activePoolBracket = useMemo(() => {
    if (!activeMeta || activeMeta.kind !== "pool") return null;
    return brackets.find((b) => b.id === activeMeta.bracketId) ?? null;
  }, [activeMeta, brackets]);

  const dayOptions = useMemo(() => {
    return Array.from({ length: Math.max(1, dayCount) }, (_, index) => index + 1);
  }, [dayCount]);

  const columns = useMemo(() => {
    const grouped: Record<ColumnKey, TimetableEntry[]> = {};
    for (const entry of entries) {
      if (entry.day !== selectedDay) continue;
      const key = buildColumnKey(entry.day, entry.tatami);
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(entry);
    }
    Object.values(grouped).forEach((column) => column.sort((a, b) => a.order_index - b.order_index));
    return grouped;
  }, [entries, selectedDay]);

  const tatamiList = useMemo(() => {
    return Array.from({ length: Math.max(1, tatamiCount) }, (_, index) => index + 1);
  }, [tatamiCount]);

  useEffect(() => {
    if (selectedDay > dayCount) {
      setSelectedDay(dayCount);
    }
  }, [selectedDay, dayCount]);

  const handleDragStart = (event: DragStartEvent) => {
    const activeId = String(event.active.id);
    if (activeId.startsWith("pool-")) {
      const bracketId = Number(activeId.replace("pool-", ""));
      setActiveMeta({ kind: "pool", bracketId });
      setPoolPreview(null);
      return;
    }
    const entryId = Number(activeId);
    const entry = entries.find((item) => item.id === entryId);
    if (entry) {
      setActiveMeta({ kind: "entry", id: entry.id, day: entry.day, tatami: entry.tatami });
    }
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) {
      setPoolPreview(null);
      return;
    }
    if (!activeMeta) return;

    if (activeMeta.kind === "pool") {
      const overId = over.id;
      const overEntry = entries.find((entry) => entry.id === Number(overId));
      let targetDay: number | null = null;
      let targetTatami: number | null = null;
      if (typeof overId === "string" && overId.startsWith("column-")) {
        const [, dayStr, tatamiStr] = overId.split("-");
        targetDay = Number(dayStr);
        targetTatami = Number(tatamiStr);
      } else if (overEntry) {
        targetDay = overEntry.day;
        targetTatami = overEntry.tatami;
      }
      if (targetDay === null || targetTatami === null) {
        setPoolPreview(null);
        return;
      }
      const columnEntries = entries
        .filter((entry) => entry.day === targetDay && entry.tatami === targetTatami)
        .sort((a, b) => a.order_index - b.order_index);
      const insertIndex =
        overEntry && overEntry.day === targetDay && overEntry.tatami === targetTatami
          ? Math.max(
              0,
              columnEntries.findIndex((entry) => entry.id === overEntry.id),
            )
          : columnEntries.length;
      setPoolPreview({ day: targetDay, tatami: targetTatami, insertIndex, bracketId: activeMeta.bracketId });
      return;
    }

    setPoolPreview(null);
    const activeId = Number(active.id);
    const overId = over.id;

    const activeEntry = entries.find((entry) => entry.id === activeId);
    if (!activeEntry) return;

    if (typeof overId === "string" && overId.startsWith("column-")) {
      const [, dayStr, tatamiStr] = overId.split("-");
      const targetDay = Number(dayStr);
      const targetTatami = Number(tatamiStr);
      if (activeEntry.tatami !== targetTatami || activeEntry.day !== targetDay) {
        setEntries((prev) =>
          prev.map((entry) =>
            entry.id === activeEntry.id ? { ...entry, tatami: targetTatami, day: targetDay } : entry,
          ),
        );
      }
      return;
    }

    const overEntryId = Number(overId);
    if (activeId === overEntryId) return;

    const overEntry = entries.find((entry) => entry.id === overEntryId);
    if (!overEntry) return;

    if (activeEntry.tatami !== overEntry.tatami || activeEntry.day !== overEntry.day) {
      setEntries((prev) =>
        prev.map((entry) =>
          entry.id === activeEntry.id ? { ...entry, tatami: overEntry.tatami, day: overEntry.day } : entry,
        ),
      );
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { over } = event;
    const sourceMeta = activeMeta;
    const preview = poolPreview;
    setActiveMeta(null);
    setPoolPreview(null);
    if (!over) return;

    const overId = over.id;
    const overEntry = entries.find((entry) => entry.id === Number(overId));

    if (sourceMeta?.kind === "pool") {
      if (!preview) return;
      const bracket = brackets.find((item) => item.id === preview.bracketId);
      if (!bracket) return;
      const columnEntries = entries
        .filter((entry) => entry.day === preview.day && entry.tatami === preview.tatami)
        .sort((a, b) => a.order_index - b.order_index);
      const insertIndex = Math.min(Math.max(preview.insertIndex, 0), columnEntries.length);
      const startTime = columnEntries[insertIndex]?.start_time ?? columnEntries.at(-1)?.end_time ?? "09:00:00";
      const newEntry: TimetableEntry = {
        id: tempIdRef.current--,
        tournament_id: tournamentId,
        entry_type: "bracket",
        day: preview.day,
        tatami: preview.tatami,
        start_time: startTime,
        end_time: startTime,
        order_index: 1,
        title: null,
        notes: null,
        bracket_id: bracket.id,
        bracket_display_name: null,
        bracket_type: bracket.type,
      };
      const reordered = [...columnEntries];
      reordered.splice(insertIndex, 0, newEntry);
      const normalized = reordered.map((entry, index) => ({ ...entry, order_index: index + 1 }));
      const normalizedMap = new Map(normalized.map((entry) => [entry.id, entry]));
      setEntries((prev) => {
        const patched = prev.map((entry) => normalizedMap.get(entry.id) ?? entry);
        const inserted = normalized.find((entry) => entry.id === newEntry.id) ?? newEntry;
        return [...patched, inserted];
      });
      return;
    }

    if (!sourceMeta || sourceMeta.kind !== "entry") return;
    const activeId = sourceMeta.id;

    const activeEntry = entries.find((entry) => entry.id === activeId);
    if (!activeEntry) return;
    const sourceDay = sourceMeta.day;
    const sourceTatami = sourceMeta.tatami;
    const sourceKey = buildColumnKey(sourceDay, sourceTatami);

    if (typeof overId === "string" && overId.startsWith("column-")) {
      const [, dayStr, tatamiStr] = overId.split("-");
      const targetDay = Number(dayStr);
      const targetTatami = Number(tatamiStr);
      const targetKey = buildColumnKey(targetDay, targetTatami);
      const columnEntries = (columns[targetKey] ?? []).filter((entry) => entry.id !== activeId);
      const reordered = [...columnEntries, { ...activeEntry, day: targetDay, tatami: targetTatami }]
        .sort((a, b) => a.order_index - b.order_index)
        .map((entry, index) => ({ ...entry, order_index: index + 1 }));

      let updated = entries.map((entry) => reordered.find((re) => re.id === entry.id) ?? entry);
      const needsSourceReindex = sourceKey !== targetKey;
      if (needsSourceReindex) {
        const sourceEntries = (columns[sourceKey] ?? [])
          .filter((entry) => entry.id !== activeId)
          .map((entry, index) => ({ ...entry, order_index: index + 1 }));
        updated = updated.map((entry) => sourceEntries.find((re) => re.id === entry.id) ?? entry);
      }
      setEntries(updated);
      return;
    }

    const overEntryId = Number(overId);
    if (activeId === overEntryId) return;

    if (!activeEntry || !overEntry) return;

    const targetKey = buildColumnKey(overEntry.day, overEntry.tatami);
    const columnEntries = columns[targetKey] ?? [];
    const activeIndex = columnEntries.findIndex((entry) => entry.id === activeId);
    const overIndex = columnEntries.findIndex((entry) => entry.id === overId);

    const reordered = arrayMove(columnEntries, activeIndex, overIndex).map((entry, index) => ({
      ...entry,
      order_index: index + 1,
      day: overEntry.day,
      tatami: overEntry.tatami,
    }));

    let updated = entries.map((entry) => reordered.find((re) => re.id === entry.id) ?? entry);
    const needsSourceReindex = sourceKey !== targetKey;
    if (needsSourceReindex) {
      const sourceEntries = (columns[sourceKey] ?? [])
        .filter((entry) => entry.id !== activeId)
        .map((entry, index) => ({ ...entry, order_index: index + 1 }));
      updated = updated.map((entry) => sourceEntries.find((re) => re.id === entry.id) ?? entry);
    }
    setEntries(updated);
  };

  const handleCreate = async () => {
    if (createPayload.day < 1 || createPayload.tatami < 1) {
      toast.error("Day and Tatami must be at least 1");
      return;
    }

    const orderIndex =
      Math.max(
        0,
        ...(entries
          .filter((entry) => entry.day === createPayload.day && entry.tatami === createPayload.tatami)
          .map((entry) => entry.order_index) ?? [0]),
      ) + 1;

    const newEntry: TimetableEntry = {
      id: tempIdRef.current--,
      tournament_id: tournamentId,
      entry_type: createPayload.entry_type,
      day: createPayload.day,
      tatami: createPayload.tatami,
      start_time: `${createPayload.start_time}:00`,
      end_time: `${createPayload.end_time}:00`,
      order_index: orderIndex,
      title: createPayload.title || null,
      notes: createPayload.notes || null,
      bracket_id: createPayload.bracket_id,
      bracket_display_name: null,
      bracket_type: null,
    };

    setEntries((prev) => [...prev, newEntry]);
    setOpenDialog(false);
    toast.success("Entry added locally");
  };

  const handleSaveTimes = async () => {
    if (entries.some((entry) => entry.day < 1 || entry.tatami < 1 || entry.order_index < 1)) {
      toast.error("Day, Tatami and order must be at least 1");
      return;
    }

    try {
      const payload = entries.map((entry) => ({
        entry_type: entry.entry_type,
        day: entry.day,
        tatami: entry.tatami,
        start_time: entry.start_time,
        end_time: entry.end_time,
        order_index: entry.order_index,
        title: entry.title,
        notes: entry.notes,
        bracket_id: entry.bracket_id,
      }));
      const refreshed = await replaceTournamentTimetable(tournamentId, payload);
      setEntries(refreshed);
      toast.success("Changes saved");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to save changes";
      toast.error(message);
    }
  };

  const handleDelete = async (entryId: number) => {
    setEntries((prev) => prev.filter((entry) => entry.id !== entryId));
  };

  const handleEditOpen = (entry: TimetableEntry) => {
    setEditEntry(entry);
    setEditPayload({
      day: entry.day,
      tatami: entry.tatami,
      title: entry.title ?? "",
      notes: entry.notes ?? "",
    });
  };

  const handleEditSave = () => {
    if (!editEntry) return;
    if (editPayload.day < 1 || editPayload.tatami < 1) {
      toast.error("Day and Tatami must be at least 1");
      return;
    }
    setEntries((prev) =>
      prev.map((entry) =>
        entry.id === editEntry.id
          ? {
              ...entry,
              day: editPayload.day,
              tatami: editPayload.tatami,
              title:
                editEntry.entry_type === "custom" || editEntry.entry_type === "break"
                  ? editPayload.title || null
                  : entry.title,
              notes:
                editEntry.entry_type === "custom" || editEntry.entry_type === "break"
                  ? editPayload.notes || null
                  : entry.notes,
            }
          : entry,
      ),
    );
    setEditEntry(null);
  };

  return (
    <div className="h-full flex-1 flex-col gap-8 p-8 md:flex">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Timetable</h1>
          <p className="text-sm text-muted-foreground">Drag and drop entries to reorder or move between tatamis.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Label htmlFor="days-count">Days</Label>
            <Input
              id="days-count"
              className="w-20"
              type="number"
              min={1}
              value={dayCount}
              onChange={(event) => setDayCount(parsePositiveInt(event.target.value))}
            />
          </div>
          <div className="flex items-center gap-2">
            <Label htmlFor="tatamis-count">Tatamis</Label>
            <Input
              id="tatamis-count"
              className="w-20"
              type="number"
              min={1}
              value={tatamiCount}
              onChange={(event) => setTatamiCount(parsePositiveInt(event.target.value))}
            />
          </div>
          <Button onClick={() => setOpenDialog(true)}>Add Entry</Button>
          <Button variant="outline" onClick={handleSaveTimes}>
            Save changes
          </Button>
        </div>
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
        onDragCancel={() => {
          setActiveMeta(null);
          setPoolPreview(null);
        }}
      >
        {SHOW_OVERLAY_FOR_POOL && activeMeta?.kind === "pool" && activePoolBracket ? (
          <DragOverlay adjustScale={false}>
            <div className="w-fit max-w-[260px] rounded-md border bg-background px-3 py-2 text-left shadow-sm">
              <div className="text-sm font-medium">
                {getBracketDisplayName(activePoolBracket.category, activePoolBracket.group_id)}
              </div>
              <div className="text-xs text-muted-foreground">
                {getBracketTypeLabel(activePoolBracket.type)} • {activePoolBracket.participants.length} people
              </div>
            </div>
          </DragOverlay>
        ) : null}
        <Card className="overflow-visible">
          <CardHeader>
            <CardTitle>Unscheduled Brackets</CardTitle>
          </CardHeader>
          <CardContent className="overflow-visible flex flex-wrap gap-2">
            {unscheduledBrackets.length === 0 && (
              <span className="text-sm text-muted-foreground">All brackets are scheduled.</span>
            )}
            {unscheduledBrackets.map((bracket) => (
              <DraggableBracketChip key={bracket.id} bracket={bracket} />
            ))}
          </CardContent>
        </Card>

        <Tabs value={String(selectedDay)} onValueChange={(value) => setSelectedDay(Number(value))}>
          <TabsList>
            {dayOptions.map((day) => (
              <TabsTrigger key={day} value={String(day)}>
                Day {day}
              </TabsTrigger>
            ))}
          </TabsList>
          {dayOptions.map((day) => (
            <TabsContent key={day} value={String(day)}>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
                {tatamiList.map((tatami) => {
                  const columnKey = buildColumnKey(day, tatami);
                  const columnEntries = columns[columnKey] ?? [];
                  const previewForColumn =
                    poolPreview && poolPreview.day === day && poolPreview.tatami === tatami ? poolPreview : null;
                  const previewBracket = previewForColumn ? bracketMap.get(previewForColumn.bracketId) : undefined;
                  return (
                    <DroppableColumn key={columnKey} id={`column-${columnKey}`}>
                      <Card className="min-h-[320px]">
                        <CardHeader>
                          <CardTitle>Tatami {tatami}</CardTitle>
                        </CardHeader>
                        <CardContent className="flex flex-col gap-3">
                          <SortableContext
                            items={columnEntries.map((entry) => entry.id)}
                            strategy={verticalListSortingStrategy}
                          >
                            {columnEntries.map((entry, index) => (
                              <div key={entry.id} className="space-y-3">
                                {previewForColumn && previewForColumn.insertIndex === index && (
                                  <div className="rounded-md border border-dashed border-primary/60 bg-primary/5 p-3 text-sm">
                                    {previewBracket
                                      ? `${getBracketDisplayName(previewBracket.category, previewBracket.group_id)}`
                                      : "Drop here"}
                                  </div>
                                )}
                                <TimetableItem
                                  entry={entry}
                                  bracket={entry.bracket_id ? bracketMap.get(entry.bracket_id) : undefined}
                                  onDelete={handleDelete}
                                  onEdit={handleEditOpen}
                                  setEntries={setEntries}
                                />
                              </div>
                            ))}
                            {previewForColumn && previewForColumn.insertIndex >= columnEntries.length && (
                              <div className="rounded-md border border-dashed border-primary/60 bg-primary/5 p-3 text-sm">
                                {previewBracket
                                  ? `${getBracketDisplayName(previewBracket.category, previewBracket.group_id)}`
                                  : "Drop here"}
                              </div>
                            )}
                          </SortableContext>
                        </CardContent>
                      </Card>
                    </DroppableColumn>
                  );
                })}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      </DndContext>

      <Dialog open={openDialog} onOpenChange={setOpenDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create timetable entry</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid gap-2">
              <Label>Type</Label>
              <Select
                value={createPayload.entry_type}
                onValueChange={(value: TimetableEntryType) =>
                  setCreatePayload((prev) => ({ ...prev, entry_type: value, bracket_id: null }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bracket">Bracket</SelectItem>
                  <SelectItem value="break">Break</SelectItem>
                  <SelectItem value="custom">Custom</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {createPayload.entry_type === "bracket" && (
              <div className="grid gap-2">
                <Label>Bracket</Label>
                <Select
                  value={createPayload.bracket_id ? String(createPayload.bracket_id) : ""}
                  onValueChange={(value) => setCreatePayload((prev) => ({ ...prev, bracket_id: Number(value) }))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select bracket" />
                  </SelectTrigger>
                  <SelectContent>
                    {unscheduledBrackets.map((bracket) => (
                      <SelectItem key={bracket.id} value={String(bracket.id)}>
                        {getBracketDisplayName(bracket.category, bracket.group_id)} • {bracket.participants.length} •{" "}
                        {getBracketTypeLabel(bracket.type)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {createPayload.entry_type !== "bracket" && (
              <div className="grid gap-2">
                <Label>Title</Label>
                <Input
                  value={createPayload.title}
                  onChange={(event) => setCreatePayload((prev) => ({ ...prev, title: event.target.value }))}
                />
              </div>
            )}
            <div className="grid grid-cols-2 gap-2">
              <div className="grid gap-2">
                <Label>Day</Label>
                <Input
                  type="number"
                  min={1}
                  value={createPayload.day}
                  onChange={(event) =>
                    setCreatePayload((prev) => ({ ...prev, day: parsePositiveInt(event.target.value) }))
                  }
                />
              </div>
              <div className="grid gap-2">
                <Label>Tatami</Label>
                <Input
                  type="number"
                  min={1}
                  value={createPayload.tatami}
                  onChange={(event) =>
                    setCreatePayload((prev) => ({ ...prev, tatami: parsePositiveInt(event.target.value) }))
                  }
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="grid gap-2">
                <Label>Start time</Label>
                <Input
                  type="time"
                  value={createPayload.start_time}
                  onChange={(event) => setCreatePayload((prev) => ({ ...prev, start_time: event.target.value }))}
                />
              </div>
              <div className="grid gap-2">
                <Label>End time</Label>
                <Input
                  type="time"
                  value={createPayload.end_time}
                  onChange={(event) => setCreatePayload((prev) => ({ ...prev, end_time: event.target.value }))}
                />
              </div>
            </div>
            <div className="grid gap-2">
              <Label>Notes</Label>
              <Input
                value={createPayload.notes}
                onChange={(event) => setCreatePayload((prev) => ({ ...prev, notes: event.target.value }))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpenDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!editEntry} onOpenChange={(open) => (!open ? setEditEntry(null) : null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit entry</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid grid-cols-2 gap-2">
              <div className="grid gap-2">
                <Label>Day</Label>
                <Input
                  type="number"
                  min={1}
                  value={editPayload.day}
                  onChange={(event) =>
                    setEditPayload((prev) => ({ ...prev, day: parsePositiveInt(event.target.value) }))
                  }
                />
              </div>
              <div className="grid gap-2">
                <Label>Tatami</Label>
                <Input
                  type="number"
                  min={1}
                  value={editPayload.tatami}
                  onChange={(event) =>
                    setEditPayload((prev) => ({ ...prev, tatami: parsePositiveInt(event.target.value) }))
                  }
                />
              </div>
            </div>
            {(editEntry?.entry_type === "custom" || editEntry?.entry_type === "break") && (
              <>
                <div className="grid gap-2">
                  <Label>Title</Label>
                  <Input
                    value={editPayload.title}
                    onChange={(event) => setEditPayload((prev) => ({ ...prev, title: event.target.value }))}
                  />
                </div>
                <div className="grid gap-2">
                  <Label>Notes</Label>
                  <Input
                    value={editPayload.notes}
                    onChange={(event) => setEditPayload((prev) => ({ ...prev, notes: event.target.value }))}
                  />
                </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditEntry(null)}>
              Cancel
            </Button>
            <Button onClick={handleEditSave}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function TimetableItem({
  entry,
  bracket,
  onDelete,
  onEdit,
  setEntries,
}: {
  entry: TimetableEntry;
  bracket?: Bracket;
  onDelete: (id: number) => void;
  onEdit: (entry: TimetableEntry) => void;
  setEntries: Dispatch<SetStateAction<TimetableEntry[]>>;
}) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: entry.id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    // Keep native sortable card visible while moving between tatamis.
    opacity: 1,
    zIndex: isDragging ? 20 : "auto",
    position: "relative" as const,
  };

  const title =
    entry.entry_type === "bracket"
      ? bracket
        ? getBracketDisplayName(bracket.category, bracket.group_id)
        : "Unknown bracket"
      : (entry.title ?? "Custom entry");

  return (
    <Card ref={setNodeRef} style={style} {...attributes} {...listeners} className="border border-muted-foreground/20">
      <CardContent className="flex flex-col gap-2 p-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <div className="text-sm font-semibold">{title}</div>
            <div className="text-xs text-muted-foreground">
              {entry.entry_type === "bracket" && bracket
                ? `${getBracketTypeLabel(bracket.type)} • ${bracket.participants.length} people`
                : entry.entry_type}
            </div>
          </div>
          <div className="flex items-center gap-1">
            <Button
              size="icon"
              variant="ghost"
              onClick={(event) => {
                event.stopPropagation();
                onEdit(entry);
              }}
            >
              <Pencil className="h-4 w-4" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              onClick={(event) => {
                event.stopPropagation();
                onDelete(entry.id);
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="flex flex-col gap-1">
            <Label>Start</Label>
            <Input
              type="time"
              value={entry.start_time.slice(0, 5)}
              onChange={(event) =>
                setEntries((prev) =>
                  prev.map((item) =>
                    item.id === entry.id ? { ...item, start_time: `${event.target.value}:00` } : item,
                  ),
                )
              }
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label>End</Label>
            <Input
              type="time"
              value={entry.end_time.slice(0, 5)}
              onChange={(event) =>
                setEntries((prev) =>
                  prev.map((item) => (item.id === entry.id ? { ...item, end_time: `${event.target.value}:00` } : item)),
                )
              }
            />
          </div>
        </div>
        {entry.notes && <div className="text-xs text-muted-foreground">{entry.notes}</div>}
      </CardContent>
    </Card>
  );
}

function DraggableBracketChip({ bracket }: { bracket: Bracket }) {
  const id = `pool-${bracket.id}`;
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({ id });
  const style = {
    transform: CSS.Transform.toString(transform),
    opacity: isDragging ? 0 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      role="button"
      tabIndex={0}
      className="select-none rounded-md border bg-background px-3 py-2 text-left cursor-grab active:cursor-grabbing"
    >
      <div className="text-sm font-medium">{getBracketDisplayName(bracket.category, bracket.group_id)}</div>
      <div className="text-xs text-muted-foreground">
        {getBracketTypeLabel(bracket.type)} • {bracket.participants.length} people
      </div>
    </div>
  );
}

function DroppableColumn({ id, children }: { id: string; children: ReactNode }) {
  const { setNodeRef } = useDroppable({ id });
  return (
    <div ref={setNodeRef} className="min-h-[320px]">
      {children}
    </div>
  );
}
