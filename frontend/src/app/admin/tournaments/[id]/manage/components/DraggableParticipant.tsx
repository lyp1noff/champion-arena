import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Participant } from "@/lib/interfaces";
import { GripVertical } from "lucide-react";
import { Badge } from "@/components/ui/badge";

// DraggableParticipant: a sortable item for use in a SortableContext
interface DraggableParticipantProps {
  participant: Participant;
  bracketId: number;
  isDragging?: boolean;
}

export default function DraggableParticipant({
  participant,
  bracketId,
  isDragging = false,
}: DraggableParticipantProps) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: `${bracketId}-${participant.seed}`,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-2 p-1.5 bg-background border rounded-md cursor-move hover:bg-accent transition-colors ${
        isDragging ? "shadow-lg" : ""
      }`}
      {...attributes}
      {...listeners}
    >
      <GripVertical className="h-4 w-4 text-muted-foreground" />
      <div className="flex-1 min-w-0">
        <div className="font-medium text-xs truncate">
          {participant.last_name} {participant.first_name}
        </div>
        <div className="text-xs text-muted-foreground truncate">{participant.coaches_last_name?.join(", ")}</div>
      </div>
      <Badge variant="secondary" className="text-xs">
        #{participant.seed}
      </Badge>
    </div>
  );
}
