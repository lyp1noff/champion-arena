import type { BracketMatch } from "@/lib/interfaces";

interface MatchCardProps {
  match: BracketMatch;
}

export default function MatchCard({ match }: MatchCardProps) {
  return (
    <div className="w-full h-20 overflow-hidden rounded-md border border-gray-200">
      <PlayerSlot
        player={match.athlete1}
        isWinner={match.winner?.id === match.athlete1?.id}
        score={match.score_athlete1}
        isFirstRound={match.round_number === 1}
        isTop={true}
      />
      <div className="h-px bg-gray-200"></div>
      <PlayerSlot
        player={match.athlete2}
        isWinner={match.winner?.id === match.athlete2?.id}
        score={match.score_athlete2}
        isFirstRound={match.round_number === 1}
        isTop={false}
      />
    </div>
  );
}

interface PlayerSlotProps {
  player:
    | {
        id: number;
        first_name: string;
        last_name: string;
      }
    | null
    | undefined;
  isWinner: boolean;
  score: number | null | undefined;
  isFirstRound: boolean;
  isTop: boolean;
}

function PlayerSlot({ player, score, isFirstRound, isTop }: PlayerSlotProps) {
  if (!player) {
    return (
      <div className={`h-10 flex items-center justify-between px-3 ${isTop ? "bg-red-800" : "bg-blue-800"} text-white`}>
        <span className="italic">{isFirstRound ? "Bye" : "TBD"}</span>
        <span>-</span>
      </div>
    );
  }

  return (
    <div className={`h-10 flex items-center justify-between px-3 ${isTop ? "bg-red-800" : "bg-blue-800"} text-white`}>
      <div className="flex items-center truncate">
        <span className="font-medium truncate">
          {player.last_name} {player.first_name}
        </span>
      </div>
      <span className="ml-2 font-bold">{score !== null ? score : "-"}</span>
    </div>
  );
}
