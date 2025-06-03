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

  const resolvedContainerHeight = (() => {
    if (containerHeight) return containerHeight;

    if (bracket) {
      if (isRoundRobin) {
        // const participantsCount = bracket.participants.length;
        // const groupsCount = Math.ceil(participantsCount / 4);
        //
        // const participantHeight = 50;
        // const groupTitleHeight = 37 + participantHeight;
        // const additionalGroupHeight = groupsCount > 1 ? 40 * groupsCount : 0;
        //
        // const estimatedHeight =
        //   participantHeight * participantsCount + groupTitleHeight * groupsCount + additionalGroupHeight;
        //
        // return estimatedHeight > maxHeight ? maxHeight : estimatedHeight;

        return undefined;
      }

      const { cardHeight, roundTitleHeight, columnGap } = getBracketDimensions(matchCardHeight);
      const estimatedHeight =
        getInitialMatchCount(bracket.participants.length) * (cardHeight + columnGap) + roundTitleHeight;

      return estimatedHeight > maxHeight ? maxHeight : estimatedHeight;
    }

    return undefined;
  })();

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
