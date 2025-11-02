"use client";

import BracketContent from "@/components/bracket/bracket-content";
import RoundRobinContent from "@/components/bracket/round-robin-content";
import { BracketMatches, BracketType } from "@/lib/interfaces";

interface BracketViewProps {
  matches: BracketMatches;
  bracketType: BracketType;
  matchCardHeight?: number;
}

export function BracketView({ matches, bracketType, matchCardHeight = 60 }: BracketViewProps) {
  const isRoundRobin = bracketType === "round_robin";

  if (isRoundRobin) {
    return <RoundRobinContent bracketMatches={matches} />;
  }

  return <BracketContent bracketMatches={matches} matchCardHeight={matchCardHeight} />;
}
