import React from "react";

import { BracketMatchAthlete, Participant } from "@/lib/interfaces";

// Accept both Participant and BracketMatchAthlete
interface ParticipantMiniCardProps {
  participant: Participant | BracketMatchAthlete;
}

export default function ParticipantMiniCard({ participant }: ParticipantMiniCardProps) {
  return (
    <div className="border rounded-md p-2 bg-muted/50 w-full">
      <div className="font-semibold text-sm">
        {participant.last_name} {participant.first_name}
      </div>
      {participant.coaches_last_name && participant.coaches_last_name.length > 0 && (
        <div className="text-xs text-muted-foreground">Coaches: {participant.coaches_last_name.join(", ")}</div>
      )}
    </div>
  );
}
