"use client";

import { Button } from "@/components/ui/button";
import { SearchablePicker } from "@/components/admin/searchable-picker";
import { Athlete } from "@/lib/interfaces";

interface BracketParticipantControlsProps {
  athletes: Athlete[];
  selectedAthleteExternalId: number | null;
  participantSeed: string;
  loading: boolean;
  onSelectAthlete: (value: number) => void;
  onSeedChange: (value: string) => void;
  onAdd: () => void;
}

function getAthleteLabel(athlete: Athlete): string {
  const coachText = Array.isArray(athlete.coaches_last_name)
    ? athlete.coaches_last_name.join(", ")
    : athlete.coaches_last_name;

  return `${athlete.last_name} ${athlete.first_name}${coachText ? ` (${coachText})` : ""}`;
}

export function BracketParticipantControls({
  athletes,
  selectedAthleteExternalId,
  participantSeed,
  loading,
  onSelectAthlete,
  onSeedChange,
  onAdd,
}: BracketParticipantControlsProps) {
  return (
    <div className="space-y-3 rounded-lg border bg-white p-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Add Participant</h2>
        <p className="text-sm text-gray-600">Athletes come from the full arena list, not only the current tournament.</p>
      </div>

      <div className="grid gap-3 md:grid-cols-[minmax(0,2fr)_120px_160px]">
        <SearchablePicker
          options={athletes.map((athlete) => {
            const externalId = athlete.external_id ?? athlete.id;
            const label = getAthleteLabel(athlete);
            return {
              value: externalId.toString(),
              label,
              keywords: label,
            };
          })}
          value={selectedAthleteExternalId?.toString()}
          placeholder="Select athlete"
          searchPlaceholder="Search athletes..."
          emptyText="No athletes found."
          onChange={(value) => onSelectAthlete(parseInt(value, 10))}
        />

        <input
          className="h-9 rounded-md border px-3 text-sm"
          placeholder="Seed"
          inputMode="numeric"
          value={participantSeed}
          onChange={(event) => onSeedChange(event.target.value)}
        />

        <Button onClick={onAdd} disabled={loading || !selectedAthleteExternalId}>
          Add To Bracket
        </Button>
      </div>
    </div>
  );
}
