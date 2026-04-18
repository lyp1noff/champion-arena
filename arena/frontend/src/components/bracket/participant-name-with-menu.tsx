"use client";

import ParticipantMiniCard from "@/components/participant-mini-card";
import { ContextMenu, ContextMenuContent, ContextMenuTrigger } from "@/components/ui/context-menu";

import { BracketMatchAthlete, Participant } from "@/lib/interfaces";

interface ParticipantNameWithMenuProps {
  participant?: Participant | BracketMatchAthlete | null;
  className?: string;
}

export function ParticipantNameWithMenu({ participant, className }: ParticipantNameWithMenuProps) {
  if (!participant) return <span className={className}>—</span>;

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <span
          className={`cursor-pointer select-none ${className || ""}`}
          onClick={(e) => {
            e.preventDefault();
            const event = new MouseEvent("contextmenu", {
              bubbles: true,
              cancelable: true,
              view: window,
              clientX: e.clientX,
              clientY: e.clientY,
            });
            (e.target as HTMLElement).dispatchEvent(event);
          }}
        >
          {participant.last_name} {participant.first_name} ({participant.coaches_last_name?.join(", ") || ""})
        </span>
      </ContextMenuTrigger>
      <ContextMenuContent>
        <ParticipantMiniCard participant={participant} />
      </ContextMenuContent>
    </ContextMenu>
  );
}
