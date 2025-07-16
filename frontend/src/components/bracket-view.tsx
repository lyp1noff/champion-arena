"use client";

import ScreenLoader from "@/components/loader";
import BracketContent from "@/components/bracket/bracket-content";
import RoundRobinContent from "@/components/bracket/round-robin-content";
import { Bracket, BracketMatches, BracketType } from "@/lib/interfaces";
import { getBracketDimensions, getInitialMatchCount } from "@/lib/utils";

const DEFAULT_MAX_HEIGHT = 9999;

interface BracketViewBaseProps {
  loading: boolean;
  matches: BracketMatches;
  matchCardHeight?: number;
  containerHeight?: number;
  maxHeight?: number;
}

interface WithBracketType {
  bracketType: BracketType;
  bracket?: never;
}

interface WithBracket {
  bracket: Bracket;
  bracketType?: never;
}

type BracketViewProps = BracketViewBaseProps & (WithBracketType | WithBracket);

function calculateOptimalHeight(
  bracket: Bracket | undefined,
  bracketType: BracketType | undefined,
  matchCardHeight: number,
  maxHeight: number,
): number | undefined {
  if (!bracket) return undefined;

  const isRoundRobin = bracketType === "round_robin" || bracket.type === "round_robin";

  if (isRoundRobin) {
    // TODO: Implement round robin height calculation when needed
    // For now, let the component size itself naturally
    return undefined;
  }

  const { cardHeight, roundTitleHeight, columnGap } = getBracketDimensions(matchCardHeight);
  const estimatedHeight =
    getInitialMatchCount(bracket.participants.length) * (cardHeight + columnGap) + roundTitleHeight;

  return Math.min(estimatedHeight, maxHeight);
}

export function BracketView({
  loading,
  matches,
  bracketType,
  bracket,
  matchCardHeight = 60,
  containerHeight,
  maxHeight = DEFAULT_MAX_HEIGHT,
}: BracketViewProps) {
  const isRoundRobin = bracketType === "round_robin" || bracket?.type === "round_robin";

  // Use provided containerHeight or calculate optimal height
  const resolvedContainerHeight =
    containerHeight ?? calculateOptimalHeight(bracket, bracketType, matchCardHeight, maxHeight);

  if (loading) {
    return (
      <div
        className="flex items-center justify-center"
        style={{ height: isRoundRobin ? 100 : resolvedContainerHeight }}
      >
        <ScreenLoader />
      </div>
    );
  }

  if (isRoundRobin) {
    return <RoundRobinContent bracketMatches={matches ?? []} containerHeight={resolvedContainerHeight} />;
  }

  return (
    <BracketContent
      bracketMatches={matches ?? []}
      matchCardHeight={matchCardHeight}
      containerHeight={resolvedContainerHeight}
    />
  );
}
