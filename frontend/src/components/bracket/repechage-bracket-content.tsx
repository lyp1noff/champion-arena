"use client";

// import { useTranslations } from "next-intl";
import { BracketMatches } from "@/lib/interfaces";
import { getBracketDimensions } from "@/lib/utils";

import { ScrollArea, ScrollBar } from "../ui/scroll-area";
import MatchCard from "./match-card";

const CONNECTOR_COLOR = "hsl(var(--foreground))";

interface RepechageBracketViewProps {
  matches: BracketMatches;
  matchCardHeight?: number;
  matchCardWidth?: number;
  medalByAthleteId?: Record<number, "gold" | "silver" | "bronze">;
}

export default function RepechageBracketContent({
  matches,
  matchCardHeight = 60,
  matchCardWidth,
  medalByAthleteId,
}: RepechageBracketViewProps) {
  // const t = useTranslations("Round");
  const { cardHeight, cardWidth, columnGap, rowGap, roundTitleHeight } = getBracketDimensions(
    matchCardHeight,
    matchCardWidth,
  );

  if (!matches.length) {
    return <div className="text-sm text-muted-foreground">No repechage matches.</div>;
  }

  const byStep = new Map<number, BracketMatches>();
  for (const item of matches) {
    const step = item.match.repechage_step ?? item.round_number;
    const current = byStep.get(step) ?? [];
    current.push(item);
    byStep.set(step, current);
  }

  const steps = Array.from(byStep.entries())
    .map(([step, value]) => ({
      step,
      matches: value.sort((a, b) => a.position - b.position),
    }))
    .sort((a, b) => a.step - b.step);

  const stepOffset = (cardHeight + rowGap) * 0.5;
  const ladderHeight = cardHeight + Math.max(0, steps.length - 1) * stepOffset;

  return (
    <ScrollArea className="flex-1 overflow-auto">
      <div className="mx-auto flex w-max items-start py-2" style={{ columnGap }}>
        {steps.map((column, columnIndex) => (
          <div
            key={`rep-step-${column.step}`}
            className="relative min-w-0"
            style={{
              minHeight: ladderHeight + roundTitleHeight + rowGap,
            }}
          >
            {/*<div*/}
            {/*  className="absolute left-0 right-0 text-center text-sm font-semibold"*/}
            {/*  style={{ top: 0, height: roundTitleHeight }}*/}
            {/*>*/}
            {/*  {column.matches[0]?.match?.round_type === "final" ? t("final") : t("round", { number: column.step })}*/}
            {/*</div>*/}
            <ul
              className="flex min-w-0 flex-col gap-3"
              style={{ marginTop: roundTitleHeight + columnIndex * stepOffset }}
            >
              {column.matches.map((item) => {
                const hasNext = columnIndex < steps.length - 1;
                const lineWidth = 1;
                const connectorX = -columnGap / 2 - lineWidth / 2;
                return (
                  <li key={item.id} className="relative">
                    {hasNext && (
                      <>
                        <div
                          style={{
                            position: "absolute",
                            right: connectorX,
                            top: cardHeight / 2,
                            width: columnGap / 2 + lineWidth / 2,
                            height: lineWidth,
                            backgroundColor: CONNECTOR_COLOR,
                          }}
                        />
                        <div
                          style={{
                            position: "absolute",
                            right: connectorX,
                            top: cardHeight / 2,
                            width: lineWidth,
                            height: stepOffset,
                            backgroundColor: CONNECTOR_COLOR,
                          }}
                        />
                        <div
                          style={{
                            position: "absolute",
                            right: -columnGap,
                            top: cardHeight / 2 + stepOffset,
                            width: columnGap / 2 + lineWidth / 2,
                            height: lineWidth,
                            backgroundColor: CONNECTOR_COLOR,
                          }}
                        />
                      </>
                    )}
                    <MatchCard
                      bracketMatch={item}
                      height={cardHeight}
                      width={cardWidth}
                      medalByAthleteId={medalByAthleteId}
                    />
                  </li>
                );
              })}
              {!column.matches.length && <li style={{ height: cardHeight + rowGap }} />}
            </ul>
          </div>
        ))}
      </div>
      <ScrollBar orientation="horizontal" />
    </ScrollArea>
  );
}
