import { BracketMatches, BracketMatchesResponse } from "@/lib/interfaces";
import MatchCard from "../match-card";
import { ScrollArea, ScrollBar } from "../ui/scroll-area";
import { getBracketDimensions } from "@/lib/utils";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";

interface BracketCardProps {
  bracketMatches: BracketMatchesResponse;
  matchCardHeight?: number;
  matchCardWidth?: number;
}

function buildRoundSlots(maxMatchesInRound: number): number[] {
  const rounds: number[] = [];
  let value = maxMatchesInRound;
  while (value >= 1) {
    rounds.push(value);
    value = value / 2;
  }
  return rounds;
}

export default function BracketContent({ bracketMatches, matchCardHeight = 80, matchCardWidth }: BracketCardProps) {
  const {
    cardHeight: fallbackCardHeight,
    cardWidth: fallbackCardWidth,
    roundTitleHeight,
    columnGap,
    rowGap,
  } = getBracketDimensions(matchCardHeight, matchCardWidth);

  const cardHeight = matchCardHeight || fallbackCardHeight;
  const cardWidth = matchCardWidth || fallbackCardWidth;

  const renderBracketSection = (matches: BracketMatches, section: string) => {
    const sortedRounds = Array.from(new Map(matches.map((m) => [m.round_number, [] as BracketMatches])).keys())
      .sort((a, b) => a - b)
      .map((round) => ({
        round,
        bracketMatches: matches.filter((m) => m.round_number === round).sort((a, b) => a.position - b.position),
      }));

    const maxMatchesInRound = 2 ** (sortedRounds.length - 1);
    const roundSlots = buildRoundSlots(maxMatchesInRound);

    return (
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-center" style={{ columnGap }}>
          {sortedRounds.map(({ round, bracketMatches }) => {
            const label =
              bracketMatches.find((m) => m.match?.round_type)?.match.round_type ??
              `Round ${round - (section === "main_matches" ? 0 : bracketMatches[0]?.round_number - 1)}`;

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
                    className="font-semibold text-center leading-none absolute"
                    style={{ fontSize: `calc(${roundTitleHeight}px * 0.8)` }}
                  >
                    {label}
                  </h2>
                </li>
                {Array.from({ length: roundSlots[round - 1] }, (_, idx) => {
                  const bracketMatch = bracketMatches[idx] ?? null;
                  const isLastRound =
                    bracketMatch?.match?.round_type === "final" || bracketMatch?.match?.round_type === "bronze";
                  const isFirstMatchEmpty =
                    bracketMatch?.round_number === 1 &&
                    (!bracketMatch.match?.athlete1 || !bracketMatch.match?.athlete2);
                  const isMatchOdd = (idx + 1) % 2 === 1;

                  const connectorX = -columnGap / 2 - 0.5;
                  const connectorY = (maxMatchesInRound / roundSlots[round - 1] / 2) * (cardHeight + rowGap);
                  const horizontalYOffset = cardHeight / 4;
                  const totalYOffset =
                    (maxMatchesInRound / roundSlots[round - 1]) * (cardHeight + rowGap) - horizontalYOffset - 0.5;

                  return (
                    <li
                      key={bracketMatch?.id || `empty-${idx + 1}`}
                      className="relative flex-1 flex items-center justify-center"
                    >
                      {bracketMatch && !isLastRound && !isFirstMatchEmpty && (
                        <>
                          <div
                            style={{
                              position: "absolute",
                              right: connectorX,
                              width: columnGap / 2 + 0.5,
                              height: 1,
                              backgroundColor: "hsl(var(--foreground))",
                            }}
                          />
                          <div
                            style={{
                              position: "absolute",
                              right: connectorX,
                              width: 1,
                              height: connectorY - horizontalYOffset,
                              [isMatchOdd ? "bottom" : "top"]: horizontalYOffset,
                              backgroundColor: "hsl(var(--foreground))",
                            }}
                          />
                          <div
                            style={{
                              position: "absolute",
                              right: -columnGap,
                              width: columnGap / 2 + 0.5,
                              height: 1,
                              [!isMatchOdd ? "bottom" : "top"]: totalYOffset,
                              backgroundColor: "hsl(var(--foreground))",
                            }}
                          />
                        </>
                      )}
                      {bracketMatch ? (
                        <MatchCard bracketMatch={bracketMatch} height={cardHeight} width={cardWidth} />
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <Tabs defaultValue="main" className="w-full">
      <TabsList>
        <TabsTrigger value="main">Main Bracket</TabsTrigger>
        {bracketMatches.repechage_a_matches.length > 0 && <TabsTrigger value="repechage_a">Repechage A</TabsTrigger>}
        {bracketMatches.repechage_b_matches.length > 0 && <TabsTrigger value="repechage_b">Repechage B</TabsTrigger>}
      </TabsList>
      <ScrollArea className="flex-1 overflow-auto">
        <TabsContent value="main">{renderBracketSection(bracketMatches.main_matches, "main_matches")}</TabsContent>
        {bracketMatches.repechage_a_matches.length > 0 && (
          <TabsContent value="repechage_a">
            {renderBracketSection(bracketMatches.repechage_a_matches, "repechage_a_matches")}
          </TabsContent>
        )}
        {bracketMatches.repechage_b_matches.length > 0 && (
          <TabsContent value="repechage_b">
            {renderBracketSection(bracketMatches.repechage_b_matches, "repechage_b_matches")}
          </TabsContent>
        )}
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </Tabs>
  );
}
