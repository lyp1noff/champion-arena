"use client";

import ScreenLoader from "@/components/loader";
import BracketContent from "@/components/bracket/bracket-content";
import RoundRobinContent from "@/components/bracket/round-robin-content";
import {BracketMatch, BracketType} from "@/lib/interfaces";

interface BracketViewProps {
  loading: boolean;
  matches: BracketMatch[];
  bracketType: BracketType;
  matchCardHeight: number;
  containerHeight?: number;
  estimatedHeight: number;
}

export function BracketView({
                              loading,
                              matches,
                              bracketType,
                              matchCardHeight,
                              containerHeight,
                              estimatedHeight,
                            }: BracketViewProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{height: estimatedHeight}}>
        <ScreenLoader/>
      </div>
    );
  }

  if (bracketType === "round_robin") {
    return <RoundRobinContent bracketMatches={matches ?? []}/>;
  }

  return (
    <BracketContent
      bracketMatches={matches ?? []}
      matchCardHeight={matchCardHeight}
      containerHeight={containerHeight}
    />
  );
}
