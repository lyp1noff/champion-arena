"use client";

import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";

import { BracketHeader } from "@/app/(main)/tournaments/[id]/components/BracketHeader";
import { type BracketHeaderUpdate, type BracketStateUpdate, useWebSocket } from "@/hooks/use-websocket";
import { X } from "lucide-react";
import { useDebounce } from "use-debounce";

import { BracketView, type Placement } from "@/components/bracket/bracket-view";
import { ChangeFlash } from "@/components/bracket/change-flash";
import { SkeletonBracketView } from "@/components/bracket/skeleton-bracket";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { getBracketMatchesById, getBracketsById } from "@/lib/api/brackets";
import { getTournamentBracketsById } from "@/lib/api/tournaments";
import { Bracket, BracketMatches, TimetableEntry, Tournament } from "@/lib/interfaces";
import { getBracketDisplayName } from "@/lib/utils";

import { ParticipantsView } from "./ParticipantsView";

interface TournamentPageContentProps {
  tournament: Tournament | null;
  brackets: Bracket[];
  timetableEntries: TimetableEntry[];
}

type BracketsById = Record<number, Bracket>;
type MatchesById = Record<number, BracketMatches>;

const sameJson = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b);

/** Keep previous objects for unchanged matches so memoized cards skip re-rendering. */
function reconcileMatches(prev: BracketMatches | undefined, next: BracketMatches): BracketMatches {
  if (!prev) return next;
  const prevById = new Map(prev.map((bm) => [bm.id, bm]));
  let unchanged = prev.length === next.length;
  const merged = next.map((bm, index) => {
    const old = prevById.get(bm.id);
    if (old && sameJson(old, bm)) {
      if (prev[index] !== old) unchanged = false;
      return old;
    }
    unchanged = false;
    return bm;
  });
  return unchanged ? prev : merged;
}

function isOlder(incoming: Bracket | BracketHeaderUpdate, current: Bracket | undefined) {
  return current?.version != null && incoming.version != null && incoming.version < current.version;
}

function toById(list: Bracket[]): BracketsById {
  return Object.fromEntries(list.map((b) => [b.id, b]));
}

function bracketPlacements(bracket: Bracket): Placement[] {
  const placements: Placement[] = [];
  if (bracket.place_1) placements.push({ place: 1 as const, athlete: bracket.place_1 });
  if (bracket.place_2) placements.push({ place: 2 as const, athlete: bracket.place_2 });
  if (bracket.place_3_a) placements.push({ place: 3 as const, athlete: bracket.place_3_a });
  if (bracket.place_3_b) placements.push({ place: 3 as const, athlete: bracket.place_3_b });
  return placements;
}

const groupKey = (day: string, tatami: string) => `${day}|${tatami}`;

export default function TournamentBrackets({ tournament, brackets, timetableEntries }: TournamentPageContentProps) {
  const t = useTranslations("TournamentPage");
  const router = useRouter();
  const searchParams = useSearchParams();
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 400);

  const urlDay = searchParams.get("day");

  const [tab, setTab] = useState("brackets");
  const [bracketsById, setBracketsById] = useState<BracketsById>(() => toById(brackets));
  const [matchesById, setMatchesById] = useState<MatchesById>({});
  const [openByGroup, setOpenByGroup] = useState<Record<string, string[]>>({});
  const [filteredEntries, setFilteredEntries] = useState<TimetableEntry[]>([]);
  const [selectedDay, setSelectedDay] = useState<string>("1");

  const matchesRef = useRef(matchesById);
  matchesRef.current = matchesById;
  /** Loaded brackets that changed while not subscribed; refetched when shown again. */
  const staleRef = useRef<Set<number>>(new Set());
  /** Bumped on every pushed state, so an older in-flight HTTP response can be dropped. */
  const pushSeqRef = useRef<Map<number, number>>(new Map());
  const inflightRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    setBracketsById(toById(brackets));
  }, [brackets]);

  const applyBracket = useCallback((bracket: Bracket) => {
    setBracketsById((prev) => {
      const current = prev[bracket.id];
      if (isOlder(bracket, current) || (current && sameJson(current, bracket))) return prev;
      return { ...prev, [bracket.id]: bracket };
    });
  }, []);

  const applyMatches = useCallback((bracketId: number, matches: BracketMatches) => {
    setMatchesById((prev) => {
      const next = reconcileMatches(prev[bracketId], matches);
      return next === prev[bracketId] ? prev : { ...prev, [bracketId]: next };
    });
  }, []);

  const fetchBracket = useCallback(
    async (bracketId: number) => {
      if (inflightRef.current.has(bracketId)) return;
      inflightRef.current.add(bracketId);
      const seq = pushSeqRef.current.get(bracketId) ?? 0;
      const [matchesResult, bracketResult] = await Promise.allSettled([
        getBracketMatchesById(bracketId),
        getBracketsById(bracketId),
      ]);
      inflightRef.current.delete(bracketId);
      if ((pushSeqRef.current.get(bracketId) ?? 0) !== seq) return;

      if (bracketResult.status === "fulfilled") applyBracket(bracketResult.value);
      if (matchesResult.status === "fulfilled") {
        staleRef.current.delete(bracketId);
        applyMatches(bracketId, matchesResult.value);
      } else {
        console.error("Error fetching bracket matches:", matchesResult.reason);
        if (!matchesRef.current[bracketId]) applyMatches(bracketId, []);
      }
    },
    [applyBracket, applyMatches],
  );

  useEffect(() => {
    if (!timetableEntries.length) return;
    const searchLower = (debouncedSearch ?? "").trim().toLowerCase();
    if (!searchLower) {
      setFilteredEntries(timetableEntries);
      return;
    }
    const result = timetableEntries.filter((entry) => {
      if (entry.entry_type !== "bracket") {
        const title = entry.title?.toLowerCase() ?? "";
        return title.includes(searchLower);
      }
      const bracket = entry.bracket_id ? bracketsById[entry.bracket_id] : undefined;
      if (!bracket) return false;
      const matchesBracketCategory = bracket.category?.toLowerCase().includes(searchLower);
      const matchesDisplayName = getBracketDisplayName(bracket.category, bracket.group_id)
        .toLowerCase()
        .includes(searchLower);
      const matchesParticipant = bracket.participants.some((participant) => {
        const firstName = participant.first_name?.toLowerCase() ?? "";
        const lastName = participant.last_name?.toLowerCase() ?? "";
        const coachLastNames = participant.coaches_last_name?.join(" ").toLowerCase() ?? "";
        return (
          firstName.includes(searchLower) || lastName.includes(searchLower) || coachLastNames.includes(searchLower)
        );
      });
      return matchesBracketCategory || matchesDisplayName || matchesParticipant;
    });
    setFilteredEntries(result);

    const days = [...new Set(result.map((entry) => String(entry.day)))];
    if (days.length === 1) {
      setSelectedDay(days[0]);
    }
  }, [debouncedSearch, timetableEntries, bracketsById]);

  const handleDayChange = (v: string) => {
    setSelectedDay(v);
    const params = new URLSearchParams(searchParams.toString());
    params.set("day", v);
    router.replace(`?${params.toString()}`, { scroll: false });
  };

  const entriesByDayTatami = useMemo(() => {
    const grouped = filteredEntries.reduce<Record<string, Record<string, TimetableEntry[]>>>((acc, entry) => {
      const dayKey = String(entry.day);
      const tatamiKey = entry.tatami;
      if (!acc[dayKey]) acc[dayKey] = {};
      if (!acc[dayKey][tatamiKey]) acc[dayKey][tatamiKey] = [];
      acc[dayKey][tatamiKey].push(entry);
      return acc;
    }, {});
    for (const tatamis of Object.values(grouped)) {
      for (const list of Object.values(tatamis)) list.sort((a, b) => a.order_index - b.order_index);
    }
    return grouped;
  }, [filteredEntries]);

  useEffect(() => {
    if (urlDay) {
      setSelectedDay(urlDay);
    } else if (tournament) {
      const start = new Date(tournament.start_date);
      const end = new Date(tournament.end_date);
      const now = new Date();

      const toDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
      const startDay = toDay(start);
      const endDay = toDay(end);
      const nowDay = toDay(now);

      const computedDay = nowDay >= startDay && nowDay <= endDay ? Math.floor((+nowDay - +startDay) / 86400000) + 1 : 1;

      const existingDays = Object.keys(entriesByDayTatami).map(Number);

      const validDay = existingDays.includes(computedDay)
        ? computedDay
        : existingDays.length > 0
          ? Math.min(...existingDays)
          : 1;

      setSelectedDay(String(validDay));
    }
  }, [urlDay, tournament, entriesByDayTatami]);

  // Brackets expanded on the visible day: these get full live state, the rest only status badges.
  const openBracketIds = useMemo(() => {
    const ids = new Set<number>();
    for (const [key, values] of Object.entries(openByGroup)) {
      if (!key.startsWith(`${selectedDay}|`)) continue;
      for (const value of values) {
        const id = Number(value);
        if (Number.isInteger(id)) ids.add(id);
      }
    }
    return [...ids].sort((a, b) => a - b);
  }, [openByGroup, selectedDay]);

  const openBracketIdsRef = useRef(openBracketIds);
  openBracketIdsRef.current = openBracketIds;
  const openKey = openBracketIds.join(",");

  useEffect(() => {
    for (const id of openBracketIdsRef.current) {
      if (!matchesRef.current[id] || staleRef.current.has(id)) void fetchBracket(id);
    }
  }, [openKey, fetchBracket]);

  const handleBracketState = useCallback(
    ({ bracket, matches }: BracketStateUpdate) => {
      pushSeqRef.current.set(bracket.id, (pushSeqRef.current.get(bracket.id) ?? 0) + 1);
      staleRef.current.delete(bracket.id);
      applyBracket(bracket);
      applyMatches(bracket.id, matches);
    },
    [applyBracket, applyMatches],
  );

  const handleBracketsUpdated = useCallback(
    (bracketIds: number[], headers: BracketHeaderUpdate[]) => {
      if (headers.length) {
        setBracketsById((prev) => {
          let next = prev;
          for (const header of headers) {
            const current = next[header.id];
            if (!current || isOlder(header, current)) continue;
            if (current.status === header.status && current.version === header.version) continue;
            if (next === prev) next = { ...prev };
            next[header.id] = { ...current, status: header.status, version: header.version };
          }
          return next;
        });
      }
      const open = new Set(openBracketIdsRef.current);
      for (const id of bracketIds) {
        // Open but pushed as a header: the server had not seen our subscription yet.
        if (open.has(id)) void fetchBracket(id);
        else if (matchesRef.current[id]) staleRef.current.add(id);
      }
    },
    [fetchBracket],
  );

  const handleReconnect = useCallback(() => {
    // Updates may have been missed while offline.
    for (const id of Object.keys(matchesRef.current)) staleRef.current.add(Number(id));
    for (const id of openBracketIdsRef.current) void fetchBracket(id);
    if (tournament?.id) {
      getTournamentBracketsById(tournament.id)
        .then((fresh) => fresh.forEach(applyBracket))
        .catch((err) => console.error("Error refreshing brackets:", err));
    }
  }, [tournament?.id, fetchBracket, applyBracket]);

  useWebSocket({
    tournamentId: String(tournament?.id),
    subscribedBracketIds: openBracketIds,
    onBracketState: handleBracketState,
    onBracketsUpdated: handleBracketsUpdated,
    onReconnect: handleReconnect,
  });

  const setGroupOpen = useCallback((key: string, values: string[]) => {
    setOpenByGroup((prev) => ({ ...prev, [key]: values }));
  }, []);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6 sm:mb-10">
        <div className={"flex flex-row gap-2 w-full"}>
          <Input
            placeholder={t("searchPlaceholder")}
            value={search}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
          />
          {search && (
            <Button type="button" onClick={() => setSearch("")} variant={"secondary"}>
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
        <Tabs defaultValue="brackets" onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="brackets">{t("brackets")}</TabsTrigger>
            <TabsTrigger value="participants">{t("participants")}</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <Tabs value={selectedDay} onValueChange={handleDayChange}>
        {Object.keys(entriesByDayTatami).length > 1 && (
          <TabsList>
            {Object.keys(entriesByDayTatami)
              .sort()
              .map((day) => (
                <TabsTrigger key={day} value={day}>
                  {t("day", { number: day })}
                </TabsTrigger>
              ))}
          </TabsList>
        )}
        {Object.entries(entriesByDayTatami).map(([day, tatamis]) => (
          <TabsContent key={day} value={day}>
            {Object.entries(tatamis).map(([tatami, tatamiEntries]) => {
              const key = groupKey(day, tatami);
              return (
                <div key={tatami} className="mt-10">
                  <h2 className="text-2xl font-bold mb-2">
                    {t("tatami")} {tatami}
                  </h2>
                  <Accordion
                    type="multiple"
                    className="w-full"
                    value={openByGroup[key] ?? []}
                    onValueChange={(values) => setGroupOpen(key, values)}
                  >
                    {tatamiEntries.map((entry) => {
                      if (entry.entry_type !== "bracket") {
                        return <CustomEntryItem key={`custom-${entry.id}`} entry={entry} />;
                      }
                      const bracket = entry.bracket_id ? bracketsById[entry.bracket_id] : undefined;
                      if (!bracket) {
                        return <MissingBracketItem key={`missing-${entry.id}`} entryId={entry.id} />;
                      }
                      return (
                        <BracketItem
                          key={bracket.id}
                          bracket={bracket}
                          time={entry.start_time}
                          matches={matchesById[bracket.id]}
                          showParticipants={tab !== "brackets"}
                        />
                      );
                    })}
                  </Accordion>
                </div>
              );
            })}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}

const BracketItem = memo(function BracketItem({
  bracket,
  time,
  matches,
  showParticipants,
}: {
  bracket: Bracket;
  time: string;
  matches: BracketMatches | undefined;
  showParticipants: boolean;
}) {
  const placements = useMemo(() => bracketPlacements(bracket), [bracket]);
  return (
    <AccordionItem value={String(bracket.id)}>
      <AccordionTrigger className="group relative isolate hover:no-underline">
        <ChangeFlash signature={bracket.status} variant="fill" className="-inset-x-2 rounded-md" />
        <BracketHeader bracket={bracket} time={time} />
      </AccordionTrigger>
      <AccordionContent>
        {showParticipants ? (
          <ParticipantsView bracket={bracket} />
        ) : matches ? (
          <BracketView matches={matches} bracketType={bracket.type} placements={placements} />
        ) : (
          <SkeletonBracketView bracketType={bracket.type} count={bracket.participants.length} />
        )}
      </AccordionContent>
    </AccordionItem>
  );
});

const CustomEntryItem = memo(function CustomEntryItem({ entry }: { entry: TimetableEntry }) {
  const t = useTranslations("TournamentPage");
  return (
    <AccordionItem value={`custom-${entry.id}`}>
      <AccordionTrigger className="group hover:no-underline">
        <div className="flex flex-col text-left">
          <span className="font-semibold">{entry.title ?? t("customEntry")}</span>
          <span className="text-sm text-muted-foreground">
            {entry.start_time.slice(0, 5)} – {entry.end_time.slice(0, 5)}
          </span>
        </div>
      </AccordionTrigger>
      <AccordionContent>
        <div className="text-sm text-muted-foreground">{entry.notes ?? "-"}</div>
      </AccordionContent>
    </AccordionItem>
  );
});

function MissingBracketItem({ entryId }: { entryId: number }) {
  const t = useTranslations("TournamentPage");
  return (
    <AccordionItem value={`missing-${entryId}`}>
      <AccordionTrigger className="group hover:no-underline">{t("unknownBracket")}</AccordionTrigger>
      <AccordionContent>
        <div className="text-sm text-muted-foreground">{t("unknownBracket")}</div>
      </AccordionContent>
    </AccordionItem>
  );
}
