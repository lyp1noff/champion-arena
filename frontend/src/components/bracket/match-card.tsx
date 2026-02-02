import { LiveBadge } from "@/components/bracket/live-badge";
import { ParticipantNameWithMenu } from "@/components/bracket/participant-name-with-menu";
import { useMatchUpdate } from "@/components/websocket-provider";

import { BracketMatch, BracketMatchAthlete } from "@/lib/interfaces";

interface MatchCardProps {
  bracketMatch: BracketMatch;
  width?: number;
  height?: number;
  medalByAthleteId?: Record<number, "gold" | "silver" | "bronze">;
}

export default function MatchCard({ bracketMatch, width = 220, height = 80, medalByAthleteId }: MatchCardProps) {
  const calculatedHeight = (height - 3) / 2;
  const calculatedFontSize = height / 5;

  // Get real-time updates for this match
  const matchUpdate = useMatchUpdate(bracketMatch.match.id);

  // Use real-time data if available, otherwise fall back to original data
  const currentScore1 = matchUpdate?.score_athlete1 ?? bracketMatch.match.score_athlete1;
  const currentScore2 = matchUpdate?.score_athlete2 ?? bracketMatch.match.score_athlete2;
  const currentStatus = matchUpdate?.status ?? bracketMatch.match.status;

  if (bracketMatch.round_number === 1 && (!bracketMatch.match?.athlete1 || !bracketMatch.match?.athlete2)) return;
  // return <div className="border border-dashed border-gray-500 rounded-md opacity-30" style={{ width, height }} />;

  return (
    <div className="relative" style={{ width }}>
      {/* Works only with 60px height */}
      {currentStatus === "started" && (
        <LiveBadge variant="rounded-t" size="sm" className="absolute right-3 z-10" style={{ bottom: `${height}px` }} />
      )}

      <div className="overflow-hidden rounded-md border" style={{ width, height }}>
        <PlayerSlot
          player={bracketMatch.match.athlete1}
          score={currentScore1}
          medal={bracketMatch.match.athlete1 ? medalByAthleteId?.[bracketMatch.match.athlete1.id] : undefined}
          isTop={true}
          height={calculatedHeight}
          width={width}
          fontSize={calculatedFontSize}
        />
        <div className="h-px" />
        <PlayerSlot
          player={bracketMatch.match.athlete2}
          score={currentScore2}
          medal={bracketMatch.match.athlete2 ? medalByAthleteId?.[bracketMatch.match.athlete2.id] : undefined}
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
  medal?: "gold" | "silver" | "bronze";
  score: number | null | undefined;
  isTop: boolean;
  height?: number;
  width?: number;
  fontSize?: number;
}

function PlayerSlot({ player, score, medal, isTop, height = 40, width = 220, fontSize = 14 }: PlayerSlotProps) {
  const bgColor = isTop ? "bg-red-800" : "bg-blue-800";
  const paddingX = Math.max(4, Math.floor(width / 25));
  const medalStripColor =
    medal === "gold" ? "#FFD700" : medal === "silver" ? "#C0C0C0" : medal === "bronze" ? "#CD7F32" : null;

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
      className={`relative flex items-center justify-between text-white ${bgColor}`}
      style={{ height, fontSize, paddingLeft: paddingX, paddingRight: paddingX }}
    >
      <span className="font-medium truncate">
        <ParticipantNameWithMenu participant={player} />
      </span>

      <div className="ml-1 min-w-4 text-right font-bold transition-all duration-300 ease-in-out">
        {score !== null ? score : "-"}
      </div>
      {medal ? (
        <span
          className="absolute right-0 top-0 h-full w-1.5"
          style={{ backgroundColor: medalStripColor ?? undefined }}
        />
      ) : null}
    </div>
  );
}
