"use client";

import { useEffect, useMemo, useState } from "react";

import { useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";

import { BracketHeader } from "@/app/(main)/tournaments/[id]/components/BracketHeader";
import { RefreshCcw, X } from "lucide-react";
import { useDebounce } from "use-debounce";

import { BracketView } from "@/components/bracket/bracket-view";
import { SkeletonBracketView } from "@/components/bracket/skeleton-bracket";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { WebSocketProvider } from "@/components/websocket-provider";

import { getBracketMatchesById } from "@/lib/api/brackets";
import { Bracket, BracketMatches, TimetableEntry, Tournament } from "@/lib/interfaces";
import { getBracketDisplayName } from "@/lib/utils";

import { ParticipantsView } from "./ParticipantsView";

interface TournamentPageContentProps {
  tournament: Tournament | null;
  brackets: Bracket[];
  timetableEntries: TimetableEntry[];
}

export default function TournamentBrackets({ tournament, brackets, timetableEntries }: TournamentPageContentProps) {
  const t = useTranslations("TournamentPage");
  const router = useRouter();
  const searchParams = useSearchParams();
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 400);

  const urlDay = searchParams.get("day");

  const [tab, setTab] = useState("brackets");
  const [loadedBracketMatches, setLoadedBracketMatches] = useState<Record<number, { matches: BracketMatches }>>({});
  const [filteredEntries, setFilteredEntries] = useState<TimetableEntry[]>([]);
  const [selectedDay, setSelectedDay] = useState<string>("1");

  const loadBracketData = async (bracketId: number, force?: boolean) => {
    if (!force && loadedBracketMatches[bracketId]) return;
    try {
      const matches = await getBracketMatchesById(bracketId);
      setLoadedBracketMatches((prev) => ({
        ...prev,
        [bracketId]: { matches },
      }));
    } catch (err) {
      console.error("Error fetching tournament bracketMatches:", err);
      setLoadedBracketMatches((prev) => ({
        ...prev,
        [bracketId]: { matches: [] },
      }));
    }
  };

  const bracketMap = useMemo(() => {
    const map = new Map<number, Bracket>();
    for (const bracket of brackets) {
      map.set(bracket.id, bracket);
    }
    return map;
  }, [brackets]);

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
      const bracket = entry.bracket_id ? bracketMap.get(entry.bracket_id) : undefined;
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
  }, [debouncedSearch, timetableEntries, bracketMap]);

  const handleDayChange = (v: string) => {
    setSelectedDay(v);
    const params = new URLSearchParams(searchParams.toString());
    params.set("day", v);
    router.replace(`?${params.toString()}`, { scroll: false });
  };

  const entriesByDayTatami = filteredEntries.reduce<Record<string, Record<string, TimetableEntry[]>>>((acc, entry) => {
    const dayKey = String(entry.day);
    const tatamiKey = entry.tatami;
    if (!acc[dayKey]) acc[dayKey] = {};
    if (!acc[dayKey][tatamiKey]) acc[dayKey][tatamiKey] = [];
    acc[dayKey][tatamiKey].push(entry);
    return acc;
  }, {});

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

      <WebSocketProvider tournamentId={String(tournament?.id)}>
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
              {Object.entries(tatamis).map(([tatami, tatamiEntries]) => (
                <div key={tatami} className="mt-10">
                  <h2 className="text-2xl font-bold mb-2">
                    {t("tatami")} {tatami}
                  </h2>
                  <Accordion
                    type="multiple"
                    className="w-full"
                    // value={openBracketIds}
                    // onValueChange={setOpenBracketIds}
                  >
                    {tatamiEntries
                      .sort((a, b) => a.order_index - b.order_index)
                      .map((entry) => {
                        if (entry.entry_type !== "bracket") {
                          return (
                            <AccordionItem key={`custom-${entry.id}`} value={`custom-${entry.id}`}>
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
                        }

                        const bracket = entry.bracket_id ? bracketMap.get(entry.bracket_id) : undefined;
                        if (!bracket) {
                          return (
                            <AccordionItem key={`missing-${entry.id}`} value={`missing-${entry.id}`}>
                              <AccordionTrigger className="group hover:no-underline">
                                {t("unknownBracket")}
                              </AccordionTrigger>
                              <AccordionContent>
                                <div className="text-sm text-muted-foreground">{t("unknownBracket")}</div>
                              </AccordionContent>
                            </AccordionItem>
                          );
                        }

                        return (
                          <AccordionItem key={bracket.id} value={String(bracket.id)}>
                            <AccordionTrigger
                              className="group hover:no-underline"
                              onClick={() => loadBracketData(bracket.id)}
                            >
                              <BracketHeader bracket={bracket} time={entry.start_time} />
                            </AccordionTrigger>
                            <AccordionContent>
                              {tab !== "brackets" ? (
                                <ParticipantsView bracket={bracket} />
                              ) : (
                                <>
                                  <div className="pb-4 flex justify-end">
                                    <button
                                      className="p-2 border rounded-full"
                                      onClick={async (e) => {
                                        e.preventDefault();
                                        e.stopPropagation();
                                        await loadBracketData(bracket.id, true);
                                      }}
                                      aria-label="Reload bracket"
                                      type="button"
                                    >
                                      <RefreshCcw className="w-5 h-5" />
                                    </button>
                                  </div>
                                  {loadedBracketMatches[bracket.id] ? (
                                    <BracketView
                                      matches={loadedBracketMatches[bracket.id].matches}
                                      bracketType={bracket.type}
                                    />
                                  ) : (
                                    <SkeletonBracketView
                                      bracketType={bracket.type}
                                      count={bracket.participants.length}
                                    />
                                  )}
                                </>
                              )}
                            </AccordionContent>
                          </AccordionItem>
                        );
                      })}
                  </Accordion>
                </div>
              ))}
            </TabsContent>
          ))}
        </Tabs>
      </WebSocketProvider>
    </div>
  );
}
