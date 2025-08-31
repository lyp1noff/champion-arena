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
    const groupedRounds = matches.reduce(
      (acc, bracketMatch) => {
        if (!acc[bracketMatch.round_number]) acc[bracketMatch.round_number] = [];
        acc[bracketMatch.round_number].push(bracketMatch);
        return acc;
      },
      {} as Record<number, BracketMatches>,
    );

    const sortedRounds = Object.entries(groupedRounds)
      .map(([roundStr, bracketMatches]) => ({
        round: Number(roundStr),
        bracketMatches: bracketMatches.sort((a, b) => a.position - b.position),
      }))
      .sort((a, b) => a.round - b.round);

    const maxMatchesInRound = Math.max(...sortedRounds.map((r) => r.bracketMatches.length), 1);

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
                    {/* {label === "bronze" ? "Bronze Match" : label} */}
                    {label}
                  </h2>
                </li>
                {bracketMatches.map((bracketMatch, idx) => {
                  const isLastRound =
                    bracketMatch.match.round_type === "final" || bracketMatch.match.round_type === "bronze";
                  const isFirstMatchEmpty =
                    bracketMatch.round_number === 1 && (!bracketMatch.match?.athlete1 || !bracketMatch.match?.athlete2);
                  const isMatchOdd = bracketMatch.position % 2 === 1;

                  const connectorX = -columnGap / 2 - 1 / 2;
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
                          <div
                            style={{
                              position: "absolute",
                              right: connectorX,
                              width: columnGap / 2 + 1 / 2,
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
                              width: columnGap / 2 + 1 / 2,
                              height: 1,
                              [!isMatchOdd ? "bottom" : "top"]: totalYOffset,
                              backgroundColor: "hsl(var(--foreground))",
                            }}
                          />
                        </>
                      )}
                      <MatchCard bracketMatch={bracketMatch} height={cardHeight} width={cardWidth} />
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
