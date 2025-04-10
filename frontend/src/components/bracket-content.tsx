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

              {matches.map((match, idx) => {
                const lineWidth = 1;
                const isFirstRound = match.round_number === 1;
                const isLastRound = match.match.round_type === "final";

                return (
                  <li
                    key={match.id || `empty-${round}-${idx}`}
                    className="relative flex-1 flex items-center justify-center"
                  >
                    {!isFirstRound && (
                      <>
                        {/* Vertical line */}
                        <div
                          style={{
                            position: "absolute",
                            left: -columnGap / 2 - lineWidth / 2,
                            width: lineWidth,
                            height: (maxMatchesInRound / matches.length / 2) * (cardHeight + columnGap),
                            backgroundColor: "hsl(var(--foreground))",
                          }}
                        />

                        {/* Horizontal line */}
                        <div
                          style={{
                            position: "absolute",
                            left: -columnGap / 2 - lineWidth / 2,
                            width: columnGap / 2 + lineWidth / 2,
                            height: lineWidth,
                            top: "50%",
                            transform: `translateY(-${lineWidth / 2}px)`,
                            backgroundColor: "hsl(var(--foreground))",
                          }}
                        />
                      </>
                    )}

                    <MatchCard bracketMatch={match} height={cardHeight} width={cardWidth} />

                    {!isLastRound && (
                      <div
                        style={{
                          position: "absolute",
                          right: -columnGap / 2 - lineWidth / 2,
                          width: columnGap / 2 + lineWidth / 2,
                          height: lineWidth,
                          backgroundColor: "hsl(var(--foreground))",
                        }}
                      />
                    )}
                  </li>
                );
              })}
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
