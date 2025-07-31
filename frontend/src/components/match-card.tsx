import { BracketMatch, BracketMatchAthlete } from "@/lib/interfaces";
import { ContextMenu, ContextMenuTrigger, ContextMenuContent } from "@/components/ui/context-menu";
import ParticipantMiniCard from "@/components/participant-mini-card";
import React, { useRef } from "react";

interface MatchCardProps {
  bracketMatch: BracketMatch;
  width?: number;
  height?: number;
}

export default function MatchCard({ bracketMatch, width = 220, height = 80 }: MatchCardProps) {
  const calculatedHeight = (height - 3) / 2;
  const calculatedFontSize = height / 5;

  if (bracketMatch.round_number === 1 && (!bracketMatch.match?.athlete1 || !bracketMatch.match?.athlete2)) return;
  // return <div className="border border-dashed border-gray-500 rounded-md opacity-30" style={{ width, height }} />;

  return (
    <div className="relative" style={{ width }}>
      {/* Works only with 60px height */}
      {bracketMatch.match.status === "started" && (
        <div
          className="absolute right-3 pl-1 pr-2 pt-0.5 rounded-t-lg text-xs font-bold z-10 flex items-center gap-1 dark:bg-secondary bg-stone-300"
          style={{ bottom: `${height}px` }}
        >
          <span className="relative flex h-2 w-2 ml-0.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-600"></span>
          </span>
          Live
        </div>
      )}

      <div className="overflow-hidden rounded-md border" style={{ width, height }}>
        <PlayerSlotWithContextMenu
          player={bracketMatch.match.athlete1}
          score={bracketMatch.match.score_athlete1}
          isWinner={bracketMatch.match.winner?.id === bracketMatch.match.athlete1?.id}
          isFirstRound={bracketMatch.round_number === 1}
          isTop={true}
          height={calculatedHeight}
          width={width}
          fontSize={calculatedFontSize}
        />
        <div className="h-px" />
        <PlayerSlotWithContextMenu
          player={bracketMatch.match.athlete2}
          score={bracketMatch.match.score_athlete2}
          isWinner={bracketMatch.match.winner?.id === bracketMatch.match.athlete2?.id}
          isFirstRound={bracketMatch.round_number === 1}
          isTop={false}
          height={calculatedHeight}
          width={width}
          fontSize={calculatedFontSize}
        />
      </div>
    </div>
  );
}

interface PlayerSlotProps {
  player: BracketMatchAthlete | null | undefined;
  isWinner: boolean;
  score: number | null | undefined;
  isFirstRound: boolean;
  isTop: boolean;
  height?: number;
  width?: number;
  fontSize?: number;
}

function PlayerSlot({ player, score, isTop, height = 40, width = 220, fontSize = 14 }: PlayerSlotProps) {
  const bgColor = isTop ? "bg-red-800" : "bg-blue-800";
  const paddingX = Math.max(4, Math.floor(width / 25));

  if (!player) {
    return (
      <div
        className={`flex items-center justify-between text-white ${bgColor}`}
        style={{ height, fontSize, paddingLeft: paddingX, paddingRight: paddingX }}
      >
        <span className="italic"></span>
        {/* <span className="italic">{isFirstRound ? "Bye" : "TBD"}</span>
        <span>-</span> */}
      </div>
    );
  }

  return (
    <div
      className={`flex items-center justify-between text-white ${bgColor}`}
      style={{ height, fontSize, paddingLeft: paddingX, paddingRight: paddingX }}
    >
      <span className="font-medium truncate">
        {player.last_name} {player.first_name} ({player.coaches_last_name?.join(", ") || "No coach"})
      </span>
      <span className="ml-2 font-bold">{score !== null ? score : "-"}</span>
    </div>
  );
}

function PlayerSlotWithContextMenu(props: PlayerSlotProps) {
  const { player } = props;
  const triggerRef = useRef<HTMLDivElement>(null);

  if (!player) {
    return <PlayerSlot {...props} />;
  }

  const handleLeftClick = (e: React.MouseEvent) => {
    e.preventDefault();
    // Simulate right-click to open context menu
    const event = new MouseEvent("contextmenu", {
      bubbles: true,
      cancelable: true,
      view: window,
      clientX: e.clientX,
      clientY: e.clientY,
    });
    triggerRef.current?.dispatchEvent(event);
  };

  return (
    <ContextMenu>
      <ContextMenuTrigger asChild>
        <div ref={triggerRef} onClick={handleLeftClick} style={{ cursor: "pointer" }}>
          <PlayerSlot {...props} />
        </div>
      </ContextMenuTrigger>
      <ContextMenuContent>
        <ParticipantMiniCard participant={player} />
      </ContextMenuContent>
    </ContextMenu>
  );
}
