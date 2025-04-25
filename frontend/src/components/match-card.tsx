import {BracketMatch, BracketMatchAthlete} from "@/lib/interfaces";

interface MatchCardProps {
  bracketMatch: BracketMatch;
  width?: number;
  height?: number;
}

export default function MatchCard({bracketMatch, width = 220, height = 80}: MatchCardProps) {
  const calculatedHeight = (height - 3) / 2;
  const calculatedFontSize = height / 5;

  if (bracketMatch.round_number === 1 && (!bracketMatch.match?.athlete1 || !bracketMatch.match?.athlete2)) return;
  // return <div className="border border-dashed border-gray-500 rounded-md opacity-30" style={{ width, height }} />;

  return (
    <div className="overflow-hidden rounded-md border" style={{width, height}}>
      <PlayerSlot
        player={bracketMatch.match.athlete1}
        isWinner={bracketMatch.match.winner?.id === bracketMatch.match.athlete1?.id}
        score={bracketMatch.match.score_athlete1}
        isFirstRound={bracketMatch.round_number === 1}
        isTop={true}
        height={calculatedHeight}
        width={width}
        fontSize={calculatedFontSize}
      />
      <div className="h-px"/>
      <PlayerSlot
        player={bracketMatch.match.athlete2}
        isWinner={bracketMatch.match.winner?.id === bracketMatch.match.athlete2?.id}
        score={bracketMatch.match.score_athlete2}
        isFirstRound={bracketMatch.round_number === 1}
        isTop={false}
        height={calculatedHeight}
        width={width}
        fontSize={calculatedFontSize}
      />
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

function PlayerSlot({player, score, isTop, height = 40, width = 220, fontSize = 14}: PlayerSlotProps) {
  const bgColor = isTop ? "bg-red-800" : "bg-blue-800";
  const paddingX = Math.max(4, Math.floor(width / 25));

  if (!player) {
    return (
      <div
        className={`flex items-center justify-between text-white ${bgColor}`}
        style={{height, fontSize, paddingLeft: paddingX, paddingRight: paddingX}}
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
      style={{height, fontSize, paddingLeft: paddingX, paddingRight: paddingX}}
    >
      <span className="font-medium truncate">
        {player.last_name} {player.first_name} ({player.coach_last_name})
      </span>
      <span className="ml-2 font-bold">{score !== null ? score : "-"}</span>
    </div>
  );
}
