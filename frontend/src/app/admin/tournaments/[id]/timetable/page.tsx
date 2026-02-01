"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Dispatch, ReactNode, SetStateAction } from "react";

import { useParams } from "next/navigation";

import {
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragStartEvent,
  PointerSensor,
  closestCenter,
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

function buildColumnKey(day: number, tatami: number) {
  return `${day}-${tatami}`;
}

export default function TimetablePage() {
  const { id } = useParams();
  const tournamentId = Number(id);

  const [entries, setEntries] = useState<TimetableEntry[]>([]);
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [activeMeta, setActiveMeta] = useState<{ id: number; day: number; tatami: number } | null>(null);
  const tempIdRef = useRef(-1);
  const [selectedDay, setSelectedDay] = useState<number>(1);
  const [openDialog, setOpenDialog] = useState(false);
  const [editEntry, setEditEntry] = useState<TimetableEntry | null>(null);
  const [editPayload, setEditPayload] = useState({ day: 1, tatami: 1 });
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

  const dayOptions = useMemo(() => {
    const days = new Set(entries.map((entry) => entry.day));
    if (days.size === 0) days.add(1);
    return Array.from(days).sort((a, b) => a - b);
  }, [entries]);

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
    const tatamis = new Set(entries.filter((e) => e.day === selectedDay).map((e) => e.tatami));
    if (tatamis.size === 0) tatamis.add(1);
    return Array.from(tatamis).sort((a, b) => a - b);
  }, [entries, selectedDay]);

  const handleDragStart = (event: DragStartEvent) => {
    const entryId = Number(event.active.id);
    const entry = entries.find((item) => item.id === entryId);
    if (entry) {
      setActiveMeta({ id: entry.id, day: entry.day, tatami: entry.tatami });
    }
  };

  const handleDragOver = (event: DragOverEvent) => {
    const { active, over } = event;
    if (!over) return;
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

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    const sourceMeta = activeMeta;
    setActiveMeta(null);
    if (!over) return;

    const activeId = Number(active.id);
    const overId = over.id;

    const activeEntry = entries.find((entry) => entry.id === activeId);
    if (!activeEntry) return;
    const sourceDay = sourceMeta?.day ?? activeEntry.day;
    const sourceTatami = sourceMeta?.tatami ?? activeEntry.tatami;
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

    const overEntry = entries.find((entry) => entry.id === overEntryId);
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
    setEditPayload({ day: entry.day, tatami: entry.tatami });
  };

  const handleEditSave = () => {
    if (!editEntry) return;
    setEntries((prev) =>
      prev.map((entry) =>
        entry.id === editEntry.id ? { ...entry, day: editPayload.day, tatami: editPayload.tatami } : entry,
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
          <Button onClick={() => setOpenDialog(true)}>Add Entry</Button>
          <Button variant="outline" onClick={handleSaveTimes}>
            Save changes
          </Button>
        </div>
      </div>

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
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragStart={handleDragStart}
              onDragOver={handleDragOver}
              onDragEnd={handleDragEnd}
            >
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
                {tatamiList.map((tatami) => {
                  const columnKey = buildColumnKey(day, tatami);
                  const columnEntries = columns[columnKey] ?? [];
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
                            {columnEntries.map((entry) => (
                              <TimetableItem
                                key={entry.id}
                                entry={entry}
                                bracket={entry.bracket_id ? bracketMap.get(entry.bracket_id) : undefined}
                                onDelete={handleDelete}
                                onEdit={handleEditOpen}
                                setEntries={setEntries}
                              />
                            ))}
                          </SortableContext>
                        </CardContent>
                      </Card>
                    </DroppableColumn>
                  );
                })}
              </div>
            </DndContext>
          </TabsContent>
        ))}
      </Tabs>

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
                        {getBracketDisplayName(bracket.category, bracket.group_id)}
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
                  onChange={(event) => setCreatePayload((prev) => ({ ...prev, day: Number(event.target.value) }))}
                />
              </div>
              <div className="grid gap-2">
                <Label>Tatami</Label>
                <Input
                  type="number"
                  min={1}
                  value={createPayload.tatami}
                  onChange={(event) => setCreatePayload((prev) => ({ ...prev, tatami: Number(event.target.value) }))}
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
                  onChange={(event) => setEditPayload((prev) => ({ ...prev, day: Number(event.target.value) }))}
                />
              </div>
              <div className="grid gap-2">
                <Label>Tatami</Label>
                <Input
                  type="number"
                  min={1}
                  value={editPayload.tatami}
                  onChange={(event) => setEditPayload((prev) => ({ ...prev, tatami: Number(event.target.value) }))}
                />
              </div>
            </div>
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
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id: entry.id });
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
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
            <div className="text-xs text-muted-foreground">{entry.entry_type}</div>
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

function DroppableColumn({ id, children }: { id: string; children: ReactNode }) {
  const { setNodeRef } = useDroppable({ id });
  return (
    <div ref={setNodeRef} className="min-h-[320px]">
      {children}
    </div>
  );
}
