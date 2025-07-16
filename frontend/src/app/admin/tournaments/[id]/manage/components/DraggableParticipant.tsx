import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Participant, Bracket } from "@/lib/interfaces";
import { GripVertical, ChevronsUpDown } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import ParticipantMiniCard from "@/components/participant-mini-card";
import {
  ContextMenu,
  ContextMenuTrigger,
  ContextMenuContent,
  ContextMenuSeparator,
} from "@/components/ui/context-menu";
import { Button } from "@/components/ui/button";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from "@/components/ui/command";
import React, { useState } from "react";

interface DraggableParticipantProps {
  participant: Participant;
  bracketId: number;
  isDragging?: boolean;
  eligibleBrackets?: Bracket[];
  onMoveParticipant?: (participant: Participant, targetBracketId: number) => void;
}

export default function DraggableParticipant({
  participant,
  bracketId,
  isDragging = false,
  eligibleBrackets = [],
  onMoveParticipant,
}: DraggableParticipantProps) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: `${bracketId}-${participant.seed}`,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const [selectedBracket, setSelectedBracket] = useState<Bracket | null>(null);
  const [popoverOpen, setPopoverOpen] = useState(false);

  const filteredBrackets = eligibleBrackets.filter((b) => b.id !== bracketId);

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
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
      </ContextMenuTrigger>
      <ContextMenuContent className="min-w-72">
        <div className="px-2 pt-2 pb-1">
          <ParticipantMiniCard participant={participant} />
        </div>
        <ContextMenuSeparator />
        <div className="flex items-center gap-2 px-2 py-2">
          <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
            <PopoverTrigger asChild>
              <Button variant="outline" role="combobox" size="sm" className="w-full justify-between">
                {selectedBracket ? selectedBracket.display_name || selectedBracket.category : "Select bracket"}
                <ChevronsUpDown className="ml-2 h-4 w-4 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-full p-0">
              <Command>
                <CommandInput placeholder="Search brackets..." />
                <CommandList>
                  <CommandEmpty>No bracket found.</CommandEmpty>
                  <CommandGroup>
                    {filteredBrackets.map((bracket) => (
                      <CommandItem
                        key={bracket.id}
                        value={bracket.display_name || bracket.category}
                        onSelect={() => {
                          setSelectedBracket(bracket);
                          setPopoverOpen(false);
                        }}
                      >
                        <div className="flex items-center gap-2">
                          {/* <div
                            className={`w-4 h-4 border rounded flex items-center justify-center ${selectedBracket?.id === bracket.id ? "bg-primary border-primary" : "border-gray-300"}`}
                          >
                            {selectedBracket?.id === bracket.id && (
                              <span className="w-3 h-3 text-white flex items-center justify-center">
                                <Check size={12} />
                              </span>
                            )}
                          </div> */}
                          {bracket.display_name || bracket.category}
                        </div>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
          <Button
            size="sm"
            className="px-3 py-1"
            disabled={!selectedBracket}
            onClick={() => {
              if (onMoveParticipant && selectedBracket) {
                onMoveParticipant(participant, selectedBracket.id);
                setSelectedBracket(null);
              }
            }}
          >
            Move
          </Button>
        </div>
      </ContextMenuContent>
    </ContextMenu>
  );
}
