import { useTranslations } from "next-intl";

import { Skeleton } from "@/components/ui/skeleton";

import { BracketType, ROUND_TYPE } from "@/lib/interfaces";
import { getBracketDimensions } from "@/lib/utils";

import { ScrollArea } from "../ui/scroll-area";

interface SkeletonBracketViewProps {
  bracketType: BracketType;
  count: number;
}

export function SkeletonBracketView({ bracketType, count }: SkeletonBracketViewProps) {
  if (bracketType === "round_robin") {
    return <RoundRobinSkeleton count={count} />;
  }
  return <EliminationSkeleton count={count} />;
}

function RoundRobinSkeleton({ count }: { count: number }) {
  return (
    <div className="flex justify-center">
      <div className="overflow-auto">
        <table className="table-auto border-collapse text-sm w-full min-w-[600px]">
          <thead>
            <tr>
              <th className="border px-2 py-1 bg-muted"></th>
              {Array.from({ length: count }).map((_, i) => (
                <th key={i} className="border px-2 py-1 bg-muted text-center font-normal text-xs">
                  <Skeleton className="h-4 w-20 mx-auto" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: count }).map((_, row) => (
              <tr key={row}>
                <td className="border px-2 py-1 bg-muted font-normal text-xs">
                  <Skeleton className="h-4 w-24" />
                </td>
                {Array.from({ length: count }).map((_, col) => (
                  <td key={col} className="border px-2 py-1 text-center">
                    {row === col ? (
                      <span className="text-muted-foreground">×</span>
                    ) : (
                      <Skeleton className="h-4 w-10 mx-auto" />
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function EliminationSkeleton({ count }: { count: number }) {
  const t = useTranslations("Round");
  const rounds = Math.ceil(Math.log2(Math.max(count, 2)));
  const maxMatches = Math.pow(2, rounds - 1);

  const { cardHeight, cardWidth, roundTitleHeight, columnGap, rowGap } = getBracketDimensions(60);

  return (
    <ScrollArea className="flex-1 overflow-auto">
      <div className="flex items-start justify-center" style={{ columnGap }}>
        {Array.from({ length: rounds }).map((_, roundIndex) => {
          const matchesInRound = Math.ceil(maxMatches / Math.pow(2, roundIndex));
          const label =
            roundIndex === rounds - 1
              ? t(ROUND_TYPE.FINAL)
              : roundIndex === rounds - 2
                ? t(ROUND_TYPE.SEMIFINAL)
                : roundIndex === rounds - 3
                  ? t(ROUND_TYPE.QUARTERFINAL)
                  : t("round", { number: roundIndex + 1 });

          return (
            <ul
              key={roundIndex}
              className="flex flex-col items-stretch relative"
              style={{
                height: maxMatches * (cardHeight + rowGap) + roundTitleHeight,
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
              {Array.from({ length: matchesInRound }).map((_, matchIndex) => (
                <li key={matchIndex} className="relative flex-1 flex items-center justify-center">
                  <Skeleton className="rounded-lg" style={{ width: cardWidth, height: cardHeight }} />
                </li>
              ))}
            </ul>
          );
        })}
      </div>
    </ScrollArea>
  );
}
