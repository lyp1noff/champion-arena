import { useTranslations } from "next-intl";

import { BracketMatches } from "@/lib/interfaces";
import { getBracketDimensions } from "@/lib/utils";

import { ScrollArea, ScrollBar } from "../ui/scroll-area";
import MatchCard from "./match-card";

interface BracketCardProps {
  bracketMatches: BracketMatches;
  matchCardHeight?: number;
  matchCardWidth?: number;
  medalByAthleteId?: Record<number, "gold" | "silver" | "bronze">;
}

const CONNECTOR_COLOR = "hsl(var(--foreground))";

function groupAndSortRounds(bracketMatches: BracketMatches) {
  const groupedRounds = bracketMatches.reduce(
    (acc, bracketMatch) => {
      if (!acc[bracketMatch.round_number]) acc[bracketMatch.round_number] = [];
      acc[bracketMatch.round_number].push(bracketMatch);
      return acc;
    },
    {} as Record<number, BracketMatches>,
  );

  return Object.entries(groupedRounds)
    .map(([roundStr, matches]) => ({
      round: Number(roundStr),
      bracketMatches: matches.sort((a, b) => a.position - b.position),
    }))
    .sort((a, b) => a.round - b.round);
}

export default function BracketContent({
  bracketMatches,
  matchCardHeight = 80,
  matchCardWidth,
  medalByAthleteId,
}: BracketCardProps) {
  const t = useTranslations("Round");
  const {
    cardHeight: fallbackCardHeight,
    cardWidth: fallbackCardWidth,
    roundTitleHeight,
    columnGap,
    rowGap,
  } = getBracketDimensions(matchCardHeight, matchCardWidth);

  const cardHeight = matchCardHeight || fallbackCardHeight;
  const cardWidth = matchCardWidth || fallbackCardWidth;
  const sortedRounds = groupAndSortRounds(bracketMatches);

  const maxMatchesInRound = Math.max(...sortedRounds.map((r) => r.bracketMatches.length));

  return (
    <ScrollArea className="flex-1 overflow-auto">
      {/* Blurred background */}
      {/* <div
        className="absolute top-0 left-0 w-full bg-background"
        style={{
          height: roundTitleHeight,
          zIndex: 5,
          pointerEvents: "none",
        }}
      /> */}

      {/* Bracket */}
      <div className="flex items-start justify-center" style={{ columnGap }}>
        {sortedRounds.map(({ round, bracketMatches }) => {
          const roundType = bracketMatches.find((m) => m.match?.round_type)?.match.round_type;
          const label = roundType && roundType !== "round" ? t(roundType) : t("round", { number: round });

          return (
            <ul
              key={round}
              className="flex flex-col items-stretch relative"
              style={{
                height: maxMatchesInRound * (cardHeight + rowGap) + roundTitleHeight,
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
                  className="font-semibold text-center leading-none absolute top-0"
                  style={{ fontSize: `calc(${roundTitleHeight}px * 0.8)` }}
                >
                  {label}
                </h2>
              </li>

              {bracketMatches.map((bracketMatch, idx) => {
                const lineWidth = 1;
                const isLastRound = bracketMatch.match.round_type === "final";
                const isFirstMatchEmpty =
                  bracketMatch.round_number === 1 && (!bracketMatch.match?.athlete1 || !bracketMatch.match?.athlete2);
                const isMatchOdd = bracketMatch.position % 2 === 1;

                const connectorX = -columnGap / 2 - lineWidth / 2;
                const connectorY = (maxMatchesInRound / bracketMatches.length / 2) * (cardHeight + rowGap);
                const horizontalYOffset = cardHeight / 4;
                const totalYOffset =
                  (maxMatchesInRound / bracketMatches.length) * (cardHeight + rowGap) - horizontalYOffset - 0.5;

                return (
                  <li
                    key={bracketMatch.id || `empty-${bracketMatch.round_number}-${idx}`}
                    className="relative flex-1 flex items-center justify-center"
                  >
                    {!isLastRound && !isFirstMatchEmpty && (
                      <>
                        {/* Horizontal line from the center of this card to the right */}
                        <div
                          style={{
                            position: "absolute",
                            right: connectorX,
                            width: columnGap / 2 + lineWidth / 2,
                            height: lineWidth,
                            backgroundColor: CONNECTOR_COLOR,
                          }}
                        />

                        {/* Vertical line from this card toward the connecting line */}
                        <div
                          style={{
                            position: "absolute",
                            right: connectorX,
                            width: lineWidth,
                            height: connectorY - horizontalYOffset,
                            [isMatchOdd ? "bottom" : "top"]: horizontalYOffset,
                            backgroundColor: CONNECTOR_COLOR,
                          }}
                        />

                        {/* Horizontal line to the next round's card */}
                        <div
                          style={{
                            position: "absolute",
                            right: -columnGap,
                            width: columnGap / 2 + lineWidth / 2,
                            height: lineWidth,
                            [!isMatchOdd ? "bottom" : "top"]: totalYOffset,
                            backgroundColor: CONNECTOR_COLOR,
                          }}
                        />
                      </>
                    )}

                    <MatchCard
                      bracketMatch={bracketMatch}
                      height={cardHeight}
                      width={cardWidth}
                      medalByAthleteId={medalByAthleteId}
                    />
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
}
