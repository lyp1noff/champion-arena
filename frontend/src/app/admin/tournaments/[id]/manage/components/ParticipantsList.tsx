import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import DraggableParticipant from "./DraggableParticipant";
import { Participant } from "@/lib/interfaces";

interface ParticipantsListProps {
  participants: Participant[];
  bracketId: number;
  draggedParticipant?: { participant: Participant; bracketId: number } | null;
}

export default function ParticipantsList({ participants, bracketId }: ParticipantsListProps) {
  return (
    <SortableContext items={participants.map((p) => `${bracketId}-${p.seed}`)} strategy={verticalListSortingStrategy}>
      <div className="space-y-2 p-3">
        {participants.map((participant) => (
          <DraggableParticipant
            key={`${bracketId}-${participant.seed}`}
            participant={participant}
            bracketId={bracketId}
          />
        ))}
      </div>
    </SortableContext>
  );
}
