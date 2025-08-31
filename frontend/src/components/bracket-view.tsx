"use client";

import BracketContent from "@/components/bracket/bracket-content";
import RoundRobinContent from "@/components/bracket/round-robin-content";
import { BracketMatchesResponse, BracketType } from "@/lib/interfaces";

interface BracketViewProps {
  matches?: BracketMatchesResponse;
  bracketType: BracketType;
  matchCardHeight?: number;
  containerHeight?: number;
  maxHeight?: number;
}

export function BracketView({ matches, bracketType, matchCardHeight = 60 }: BracketViewProps) {
  const isRoundRobin = bracketType === "round_robin";

  if (!matches) {
    return;
  }

  if (isRoundRobin) {
    return <RoundRobinContent bracketMatches={matches.main_matches ?? []} />;
  }

  return <BracketContent bracketMatches={matches ?? []} matchCardHeight={matchCardHeight} />;
}
