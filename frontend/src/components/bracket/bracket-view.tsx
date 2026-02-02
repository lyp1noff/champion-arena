"use client";

import BracketContent from "@/components/bracket/bracket-content";
import MatchCard from "@/components/bracket/match-card";
import RoundRobinContent from "@/components/bracket/round-robin-content";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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

  const mainMatches = matches.filter((item) => item.match?.stage !== "repechage");
  const repechageA = matches.filter((item) => item.match?.stage === "repechage" && item.match?.repechage_side === "A");
  const repechageB = matches.filter((item) => item.match?.stage === "repechage" && item.match?.repechage_side === "B");
  const hasRepechage = repechageA.length > 0 || repechageB.length > 0;

  if (!hasRepechage) {
    return <BracketContent bracketMatches={mainMatches} matchCardHeight={matchCardHeight} />;
  }

  return (
    <Tabs defaultValue="main" className="space-y-4">
      <TabsList>
        <TabsTrigger value="main">Main</TabsTrigger>
        <TabsTrigger value="a">Repechage A</TabsTrigger>
        <TabsTrigger value="b">Repechage B</TabsTrigger>
      </TabsList>
      <TabsContent value="main">
        <BracketContent bracketMatches={mainMatches} matchCardHeight={matchCardHeight} />
      </TabsContent>
      <TabsContent value="a">
        <RepechageLadder matches={repechageA} />
      </TabsContent>
      <TabsContent value="b">
        <RepechageLadder matches={repechageB} />
      </TabsContent>
    </Tabs>
  );
}

function RepechageLadder({ matches }: { matches: BracketMatches }) {
  if (!matches.length) {
    return <div className="text-sm text-muted-foreground">No repechage matches.</div>;
  }
  const sorted = [...matches].sort((a, b) => {
    const stepA = a.match.repechage_step ?? 0;
    const stepB = b.match.repechage_step ?? 0;
    return stepA - stepB;
  });
  return (
    <div className="flex flex-col gap-3 py-2">
      {sorted.map((item, index) => (
        <div key={item.id} className="max-w-[320px]" style={{ marginLeft: `${index * 28}px` }}>
          <MatchCard bracketMatch={item} height={60} width={280} />
        </div>
      ))}
    </div>
  );
}
