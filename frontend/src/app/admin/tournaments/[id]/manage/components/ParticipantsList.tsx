import { SortableContext, verticalListSortingStrategy } from "@dnd-kit/sortable";
import DraggableParticipant from "./DraggableParticipant";
import { Participant, Bracket } from "@/lib/interfaces";

interface ParticipantsListProps {
  participants: Participant[];
  bracketId: number;
  draggedParticipant?: { participant: Participant; bracketId: number } | null;
  eligibleBrackets?: Bracket[];
  onMoveParticipant?: (participant: Participant, targetBracketId: number) => void;
}

export default function ParticipantsList({
  participants,
  bracketId,
  eligibleBrackets = [],
  onMoveParticipant,
}: ParticipantsListProps) {
  return (
    <SortableContext items={participants.map((p) => `${bracketId}-${p.seed}`)} strategy={verticalListSortingStrategy}>
      <div className="space-y-2 p-3">
        {participants.map((participant) => (
          <DraggableParticipant
            key={`${bracketId}-${participant.seed}`}
            participant={participant}
            bracketId={bracketId}
            eligibleBrackets={eligibleBrackets}
            onMoveParticipant={onMoveParticipant}
          />
        ))}
      </div>
    </SortableContext>
  );
}
