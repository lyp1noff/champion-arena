"use client";

import { Button } from "@/components/ui/button";
import { SearchablePicker } from "@/components/admin/searchable-picker";
import { Bracket, BracketParticipant } from "@/lib/interfaces";

interface BracketParticipantTableProps {
  participants: BracketParticipant[];
  brackets: Bracket[];
  selectedBracketId: number;
  loading: boolean;
  moveTargets: Record<number, string>;
  seedEdits: Record<number, string>;
  onMoveTargetChange: (participantId: number, value: string) => void;
  onSeedEditChange: (participantId: number, value: string) => void;
  onSeedSave: (participantId: number) => void;
  onMove: (participantId: number) => void;
  onRemove: (participantId: number) => void;
}

export function BracketParticipantTable({
  participants,
  brackets,
  selectedBracketId,
  loading,
  moveTargets,
  seedEdits,
  onMoveTargetChange,
  onSeedEditChange,
  onSeedSave,
  onMove,
  onRemove,
}: BracketParticipantTableProps) {
  return (
    <div className="overflow-hidden rounded-lg border bg-white">
      <div className="grid grid-cols-[160px_minmax(0,1fr)_minmax(0,260px)_100px] bg-gray-50 px-4 py-3 text-sm font-medium text-gray-700">
        <div>Seed</div>
        <div>Athlete</div>
        <div>Move</div>
        <div>Remove</div>
      </div>

      {participants.length === 0 ? (
        <div className="px-4 py-6 text-sm text-gray-500">No participants in this bracket.</div>
      ) : (
        participants.map((participant) => (
          <div
            key={participant.id}
            className="grid grid-cols-[160px_minmax(0,1fr)_minmax(0,260px)_100px] items-center gap-3 border-t px-4 py-3 text-sm"
          >
            <div className="flex items-center gap-2">
              <input
                className="h-9 w-20 rounded-md border px-3 text-sm"
                inputMode="numeric"
                value={seedEdits[participant.id] ?? String(participant.seed)}
                onChange={(event) => onSeedEditChange(participant.id, event.target.value)}
              />
              <Button
                variant="outline"
                onClick={() => onSeedSave(participant.id)}
                disabled={loading || (seedEdits[participant.id] ?? String(participant.seed)) === String(participant.seed)}
              >
                Save
              </Button>
            </div>
            <div>
              {participant.athlete ? `${participant.athlete.last_name} ${participant.athlete.first_name}` : "Empty"}
            </div>
            <div className="flex min-w-0 gap-2">
              <div className="min-w-0 flex-1">
                <SearchablePicker
                  options={brackets
                    .filter((bracket) => bracket.external_id !== selectedBracketId)
                    .map((bracket) => ({
                      value: bracket.external_id.toString(),
                      label: bracket.display_name || bracket.category,
                      keywords: `${bracket.display_name || bracket.category} ${bracket.category}`,
                    }))}
                  value={moveTargets[participant.id]}
                  placeholder="Target bracket"
                  searchPlaceholder="Search brackets..."
                  emptyText="No brackets found."
                  onChange={(value) => onMoveTargetChange(participant.id, value)}
                />
              </div>
              <Button
                variant="outline"
                onClick={() => onMove(participant.id)}
                disabled={loading || !moveTargets[participant.id]}
              >
                Move
              </Button>
            </div>
            <div>
              <Button variant="destructive" className="w-full" onClick={() => onRemove(participant.id)} disabled={loading}>
                Remove
              </Button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
