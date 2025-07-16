import { Participant } from "@/lib/interfaces";
import React from "react";

interface ParticipantMiniCardProps {
  participant: Participant;
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
