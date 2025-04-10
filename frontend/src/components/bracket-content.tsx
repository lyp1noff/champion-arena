"use client";

import { useEffect, useState } from "react";
import { BracketMatches } from "@/lib/interfaces";
import MatchCard from "./match-card";
import { ScrollArea, ScrollBar } from "./ui/scroll-area";
import { Button } from "./ui/button";
import { Maximize2, Minimize2 } from "lucide-react";
import { getBracketDimensions } from "@/lib/utils";

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
  const [fullscreen, setFullscreen] = useState(false);

  const { cardHeight, cardWidth, roundTitleHeight, columnGap } = getBracketDimensions(matchCardHeight, matchCardWidth);

  // Prevent body scroll when fullscreen
  useEffect(() => {
    if (fullscreen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [fullscreen]);

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

  const Bracket = (
    <div className="relative w-full h-full">
      {/* Кнопка фуллскрина */}
      <div className="absolute top-2 right-2 z-20">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setFullscreen(!fullscreen)}
          aria-label={fullscreen ? "Выйти из фуллскрина" : "Во весь экран"}
        >
          {fullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </Button>
      </div>

      {/* Blurred фон под заголовками */}
      <div
        className="absolute top-0 left-0 w-full bg-background"
        style={{
          height: roundTitleHeight + 2,
          zIndex: 5,
          pointerEvents: "none",
        }}
      />

      <ScrollArea className="h-full w-full overflow-auto">
        <div className="flex items-start justify-center" style={{ columnGap }}>
          {sortedRounds.map(({ round, matches }) => {
            const label = matches.find((m) => m.match?.round_type)?.match.round_type ?? `round ${round}`;

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
                    className="text-sm font-semibold text-center leading-none relative z-10"
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
    </div>
  );

  if (fullscreen) {
    return (
      <div className="fixed inset-0 bg-background z-[100] overflow-auto p-4">
        <div className="h-full w-full">{Bracket}</div>
      </div>
    );
  }

  return containerHeight ? (
    <div className="flex w-full" style={{ height: containerHeight }}>
      {Bracket}
    </div>
  ) : (
    Bracket
  );
}
