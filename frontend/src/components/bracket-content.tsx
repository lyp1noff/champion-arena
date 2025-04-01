import { BracketMatches } from "@/lib/interfaces";
import MatchCard from "./match-card";
import { ScrollArea, ScrollBar } from "./ui/scroll-area";

interface BracketCardProps {
  bracketMatches: BracketMatches;
  matchCardHeight?: number;
  matchCardWidth?: number;
  containerHeight?: number;
}

export default function BracketContent({
  bracketMatches,
  matchCardHeight = 80,
  matchCardWidth,
  containerHeight,
}: BracketCardProps) {
  const cardHeight = matchCardHeight;
  const cardWidth = matchCardWidth ?? cardHeight * 3;
  const roundTitleHeight = cardHeight / 3;
  const columnGap = (cardHeight / 8) * 2;

  const groupedRounds = bracketMatches.reduce((acc, match) => {
    if (!acc[match.round_number]) acc[match.round_number] = [];
    acc[match.round_number].push(match);
    return acc;
  }, {} as Record<number, BracketMatches>);

  const sortedRounds = Object.entries(groupedRounds)
    .map(([roundStr, matches]) => ({
      round: Number(roundStr),
      matches: matches.sort((a, b) => a.position - b.position),
    }))
    .sort((a, b) => a.round - b.round);

  const maxMatchesInRound = Math.max(...sortedRounds.map((r) => r.matches.length));

  const content = (
    <ScrollArea className="flex-1 overflow-auto">
      {/* Blurred background */}
      <div
        className="absolute top-0 left-0 w-full bg-background"
        style={{
          height: roundTitleHeight,
          zIndex: 5,
          pointerEvents: "none",
        }}
      />

      {/* Bracket */}
      <div className="flex items-start justify-center" style={{ columnGap }}>
        {sortedRounds.map(({ round, matches }) => {
          const label = matches.find((m) => m.match?.round_type)?.match.round_type ?? `Round ${round}`;

          return (
            <ul
              key={round}
              className="flex flex-col items-stretch relative"
              style={{
                height: maxMatchesInRound * (cardHeight + columnGap) + roundTitleHeight,
              }}
            >
              <li
                style={{
                  height: roundTitleHeight,
                  position: "sticky",
                  top: 0,
                  zIndex: 10,
                }}
                className="flex items-center justify-center"
              >
                <h2
                  className="text-sm font-semibold text-center leading-none"
                  style={{ fontSize: `calc(${roundTitleHeight}px * 0.8)` }}
                >
                  {label}
                </h2>
              </li>

              {matches.map((match, idx) => (
                <li key={match.id || `empty-${round}-${idx}`} className="flex-1 flex items-center justify-center">
                  <MatchCard bracketMatch={match} height={cardHeight} width={cardWidth} />
                </li>
              ))}
            </ul>
          );
        })}
      </div>
      <ScrollBar orientation="horizontal" />
    </ScrollArea>
  );

  return containerHeight ? (
    <div className="flex" style={{ height: containerHeight }}>
      {content}
    </div>
  ) : (
    content
  );
}
