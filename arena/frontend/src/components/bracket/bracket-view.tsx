"use client";

import BracketContent from "@/components/bracket/bracket-content";
import RepechageBracketContent from "@/components/bracket/repechage-bracket-content";
import RoundRobinContent from "@/components/bracket/round-robin-content";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { BracketMatchAthlete, BracketMatches, BracketType } from "@/lib/interfaces";

interface BracketViewProps {
  matches: BracketMatches;
  bracketType: BracketType;
  matchCardHeight?: number;
  placements?: Placement[];
}

export function BracketView({ matches, bracketType, matchCardHeight = 60, placements = [] }: BracketViewProps) {
  const isRoundRobin = bracketType === "round_robin";

  if (isRoundRobin) {
    return <RoundRobinContent bracketMatches={matches} />;
  }

  const mainMatches = matches.filter((item) => item.match?.stage !== "repechage");
  const repechageA = matches.filter((item) => item.match?.stage === "repechage" && item.match?.repechage_side === "A");
  const repechageB = matches.filter((item) => item.match?.stage === "repechage" && item.match?.repechage_side === "B");
  const hasRepechage = repechageA.length > 0 || repechageB.length > 0;
  const medalByAthleteId = getMedalByAthleteId(placements);

  if (!hasRepechage) {
    return (
      <div className="space-y-3">
        <PlacementsRow placements={placements} />
        <BracketContent
          bracketMatches={mainMatches}
          matchCardHeight={matchCardHeight}
          medalByAthleteId={medalByAthleteId}
        />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <PlacementsRow placements={placements} />
      <Tabs defaultValue="main" className="space-y-4">
        <TabsList>
          <TabsTrigger value="main">Main</TabsTrigger>
          <TabsTrigger value="a">Repechage A</TabsTrigger>
          <TabsTrigger value="b">Repechage B</TabsTrigger>
        </TabsList>
        <TabsContent value="main">
          <BracketContent
            bracketMatches={mainMatches}
            matchCardHeight={matchCardHeight}
            medalByAthleteId={medalByAthleteId}
          />
        </TabsContent>
        <TabsContent value="a">
          <RepechageBracketContent
            matches={repechageA}
            matchCardHeight={matchCardHeight}
            medalByAthleteId={medalByAthleteId}
          />
        </TabsContent>
        <TabsContent value="b">
          <RepechageBracketContent
            matches={repechageB}
            matchCardHeight={matchCardHeight}
            medalByAthleteId={medalByAthleteId}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export type Placement = {
  place: 1 | 2 | 3;
  athlete: BracketMatchAthlete;
};

function getPlaceBadgeClass(place: 1 | 2 | 3) {
  if (place === 1) return "border-amber-500/60 bg-amber-400/25 text-amber-700 dark:text-amber-300";
  if (place === 2) return "border-slate-400/60 bg-slate-300/30 text-slate-700 dark:text-slate-200";
  return "border-orange-500/60 bg-orange-400/25 text-orange-700 dark:text-orange-300";
}

function PlacementsRow({ placements }: { placements: Placement[] }) {
  if (!placements.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {placements.map((item, idx) => (
        <div
          key={`${item.place}-${item.athlete.id}-${idx}`}
          className={`rounded-md border px-2 py-1 text-xs font-medium ${getPlaceBadgeClass(item.place)}`}
        >
          {item.place}. {item.athlete.last_name} {item.athlete.first_name}
        </div>
      ))}
    </div>
  );
}

function getMedalByAthleteId(placements: Placement[]): Record<number, "gold" | "silver" | "bronze"> {
  return placements.reduce<Record<number, "gold" | "silver" | "bronze">>((acc, item) => {
    if (item.place === 1) acc[item.athlete.id] = "gold";
    if (item.place === 2) acc[item.athlete.id] = "silver";
    if (item.place === 3) acc[item.athlete.id] = "bronze";
    return acc;
  }, {});
}
