import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users } from "lucide-react";
import { Bracket, Participant } from "@/lib/interfaces";
import { ContextMenu, ContextMenuTrigger, ContextMenuContent, ContextMenuItem } from "@/components/ui/context-menu";

interface BracketCardProps {
  bracket: Bracket;
  isSelected: boolean;
  onSelect: () => void;
  participants: Participant[];
  onDeleteBracket: (bracket: Bracket) => void;
  onEditBracket: (bracket: Bracket) => void;
}

export default function BracketCard({
  bracket,
  isSelected,
  onSelect,
  participants,
  onDeleteBracket,
  onEditBracket,
}: BracketCardProps) {
  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <Card
          className={`cursor-pointer transition-all hover:shadow-md ${isSelected ? "ring-2 ring-primary" : ""}`}
          onClick={onSelect}
        >
          <CardHeader className="pb-2">
            <CardTitle className="text-m">{bracket.display_name || bracket.category}</CardTitle>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                <span>{participants.length}</span>
              </div>
              {bracket.start_time && (
                <div className="flex items-center gap-1">
                  <span>{bracket.start_time.slice(0, 5)}</span>
                </div>
              )}
              <div className="flex items-center gap-1">
                <span>Tatami {bracket.tatami}</span>
              </div>
            </div>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="flex items-center gap-2">
              <Badge variant={bracket.type === "single_elimination" ? "default" : "secondary"}>
                {bracket.type === "single_elimination" ? "Single Elimination" : "Round Robin"}
              </Badge>
              <Badge
                variant={
                  bracket.status === "pending" ? "secondary" : bracket.status === "started" ? "destructive" : "outline"
                }
              >
                {bracket.status.charAt(0).toUpperCase() + bracket.status.slice(1)}
              </Badge>
            </div>
          </CardContent>
        </Card>
      </ContextMenuTrigger>
      <ContextMenuContent>
        <ContextMenuItem onClick={() => onEditBracket(bracket)}>Edit</ContextMenuItem>
        <ContextMenuItem onClick={() => onDeleteBracket(bracket)}>Delete Bracket</ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
}
