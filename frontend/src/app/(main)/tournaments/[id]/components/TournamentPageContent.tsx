"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { CalendarDays, MapPin, RefreshCcw, Trophy, Users, X } from "lucide-react";
import { WebSocketProvider } from "@/components/websocket-provider";
import { BracketView } from "@/components/bracket-view";
import { ParticipantsView } from "./ParticipantsView";
import { getBracketMatchesById } from "@/lib/api/brackets";
import { getBracketDisplayName } from "@/lib/utils";
import { useDebounce } from "use-debounce";
import { Card, CardContent } from "@/components/ui/card";
import { DateRange } from "@/components/date-range";
import ScreenLoader from "@/components/loader";
import { Bracket, BracketMatches, Tournament } from "@/lib/interfaces";
import { useTranslations } from "next-intl";

import Image from "next/image";
import { useLocale } from "next-intl";

const cdnUrl = process.env.NEXT_PUBLIC_CDN_URL;

interface TournamentPageContentProps {
  tournament: Tournament | null;
  brackets: Bracket[];
}

export default function TournamentPageContent({ tournament, brackets }: TournamentPageContentProps) {
  const locale = useLocale();
  const t = useTranslations("TournamentPage");
  const router = useRouter();
  const searchParams = useSearchParams();
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 400);

  const urlDay = searchParams.get("day");

  const [tab, setTab] = useState("brackets");
  const [loading, setLoading] = useState(true);
  const [loadedBracketMatches, setLoadedBracketMatches] = useState<Record<number, { matches: BracketMatches }>>({});
  const [filteredBrackets, setFilteredBrackets] = useState<Bracket[]>([]);
  const [openBracketIds, setOpenBracketIds] = useState<string[]>([]);
  const [selectedDay, setSelectedDay] = useState<string>("1");

  const loadBracketData = async (bracketId: number, force?: true) => {
    if (!force && loadedBracketMatches[bracketId]) return;
    setLoading(true);
    try {
      const matches = await getBracketMatchesById(bracketId);
      setLoadedBracketMatches((prev) => ({
        ...prev,
        [bracketId]: { matches },
      }));
      setOpenBracketIds((prev) => [...prev, String(bracketId)]);
    } catch (err) {
      console.error("Error fetching tournament bracketMatches:", err);
      setLoadedBracketMatches((prev) => ({
        ...prev,
        [bracketId]: { matches: [] },
      }));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tournament && brackets.length > 0) {
      setLoading(false);
    }
  }, [tournament, brackets]);

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

      setSelectedDay(
        nowDay >= startDay && nowDay <= endDay ? String(Math.floor((+nowDay - +startDay) / 86400000) + 1) : "1",
      );
    }
  }, [urlDay, tournament]);

  useEffect(() => {
    if (!brackets.length) return;
    const searchLower = (debouncedSearch ?? "").trim().toLowerCase();
    if (!searchLower) {
      setFilteredBrackets(brackets);
      return;
    }
    const result = brackets.filter((bracket) => {
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
    setFilteredBrackets(result);

    const days = [...new Set(result.map((b) => String(b.day ?? 1)))];
    if (days.length === 1) {
      setSelectedDay(days[0]);
    }
  }, [debouncedSearch, brackets]);

  const handleDayChange = (v: string) => {
    setSelectedDay(v);
    setOpenBracketIds([]);
    const params = new URLSearchParams(searchParams.toString());
    params.set("day", v);
    router.replace(`?${params.toString()}`, { scroll: false });
  };

  const bracketsByDayTatami = filteredBrackets.reduce<Record<string, Record<string, typeof brackets>>>(
    (acc, bracket) => {
      const dayKey = String(bracket.day ?? 1);
      const tatamiKey = bracket.tatami ?? t("unknownTatami");
      if (!acc[dayKey]) acc[dayKey] = {};
      if (!acc[dayKey][tatamiKey]) acc[dayKey][tatamiKey] = [];
      acc[dayKey][tatamiKey].push(bracket);
      return acc;
    },
    {},
  );

  const uniqueParticipantsCount = new Set(brackets.flatMap((b) => b.participants.map((p) => p.athlete_id))).size;

  return (
    <WebSocketProvider tournamentId={String(tournament?.id)}>
      <div className="container py-10 mx-auto">
        <h1 className="text-2xl font-bold mb-10">{tournament ? tournament.name : t("tournament")}</h1>

        {tournament && (
          <Card className="mb-10 shadow-lg rounded-2xl overflow-hidden">
            <CardContent className="p-0 flex flex-col sm:flex-row">
              <div className="relative w-full h-auto sm:w-64 sm:h-64 bg-muted flex items-center justify-center">
                <Image
                  src={tournament.image_url ? `${cdnUrl}/${tournament.image_url}` : "/tournament.svg"}
                  alt={tournament.name}
                  width={500}
                  height={500}
                  className="object-contain w-full h-auto sm:w-64 sm:h-64 sm:object-cover"
                />
              </div>

              <div className="p-6 flex flex-col justify-center gap-3 text-base">
                <div className="flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-muted-foreground" />
                  <span>{tournament.location || t("unknownLocation")}</span>
                </div>

                <div className="flex items-center gap-2">
                  <CalendarDays className="w-5 h-5 text-muted-foreground" />
                  <span>
                    <DateRange start={tournament.start_date} end={tournament.end_date} locale={locale} />
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-muted-foreground" />
                  <span>
                    {t("categoriesCount")}: {brackets.length}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-muted-foreground" />
                  <span>
                    {t("participantsCount")}: {uniqueParticipantsCount}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

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

        {loading && <ScreenLoader fullscreen />}
        {/*{error && <p className="text-red-500">{error}</p>}*/}

        <Tabs value={selectedDay} onValueChange={handleDayChange}>
          <TabsList>
            {Object.keys(bracketsByDayTatami).length > 0 ? (
              Object.keys(bracketsByDayTatami)
                .sort()
                .map((day) => (
                  <TabsTrigger key={day} value={day}>
                    {t("day", { number: day })}
                  </TabsTrigger>
                ))
            ) : (
              <TabsTrigger value="1" disabled>
                {t("day", { number: 1 })}
              </TabsTrigger>
            )}
          </TabsList>

          {Object.entries(bracketsByDayTatami).map(([day, tatamis]) => (
            <TabsContent key={day} value={day}>
              {Object.entries(tatamis).map(([tatami, tatamiBrackets]) => (
                <div key={tatami} className="mt-10">
                  <h2 className="text-2xl font-bold mb-2">
                    {t("tatami")} {tatami}
                  </h2>
                  <Accordion
                    type="multiple"
                    className="w-full"
                    value={openBracketIds}
                    onValueChange={setOpenBracketIds}
                  >
                    {tatamiBrackets.map((bracket) => (
                      <AccordionItem key={bracket.id} value={String(bracket.id)}>
                        <AccordionTrigger
                          className="group flex w-full items-center justify-between text-lg font-medium hover:no-underline"
                          onClick={() => {
                            if (!loadedBracketMatches[bracket.id]) {
                              loadBracketData(bracket.id);
                            }
                          }}
                        >
                          <div className="flex w-full flex-col sm:flex-row sm:items-center gap-1 sm:gap-4 sm:justify-between">
                            <span className="text-base font-semibold group-hover:underline underline-offset-4">
                              {getBracketDisplayName(bracket.category, bracket.group_id)}
                            </span>

                            <div className="flex items-center gap-2 text-sm text-muted-foreground sm:justify-end pr-4">
                              <span className="tabular-nums">
                                {(bracket.start_time && bracket.start_time.slice(0, 5)) || "-"}
                              </span>
                              <span>|</span>
                              <span className="tabular-nums">
                                {t("participantsCount")}:{" "}
                                <span className="inline-block" style={{ minWidth: "3ch" }}>
                                  {bracket.participants.length || "-"}
                                </span>
                              </span>
                            </div>
                          </div>
                        </AccordionTrigger>
                        <AccordionContent>
                          {tab !== "brackets" ? (
                            <ParticipantsView bracket={bracket} />
                          ) : (
                            loadedBracketMatches[bracket.id] && (
                              <div>
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
                                <BracketView
                                  matches={loadedBracketMatches[bracket.id].matches}
                                  bracketType={bracket.type}
                                />
                              </div>
                            )
                          )}
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </div>
              ))}
            </TabsContent>
          ))}
        </Tabs>

        {!loading && brackets.length === 0 && <p className="text-gray-500">{t("noData")}</p>}
      </div>
    </WebSocketProvider>
  );
}
