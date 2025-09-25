"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getTournamentBracketsById, getTournamentById } from "@/lib/api/tournaments";
import { Bracket, BracketMatches, Tournament } from "@/lib/interfaces";
import ScreenLoader from "@/components/loader";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { getBracketMatchesById } from "@/lib/api/brackets";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useTranslations } from "next-intl";
import { BracketView } from "@/components/bracket-view";
import { ParticipantsView } from "./components/ParticipantsView";
import { Input } from "@/components/ui/input";
import { useDebounce } from "use-debounce";
import { WebSocketProvider } from "@/components/websocket-provider";
import { Users, CalendarDays, MapPin, Trophy, RefreshCcw, X } from "lucide-react";
import Image from "next/image";
import { Card, CardContent } from "@/components/ui/card";
import { DateRange } from "@/components/date-range";
import { Button } from "@/components/ui/button";

const cdnUrl = process.env.NEXT_PUBLIC_CDN_URL;

export default function TournamentPage() {
  const t = useTranslations("TournamentPage");
  const { id } = useParams();
  const [tab, setTab] = useState("brackets");
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [tournament, setTournament] = useState<Tournament>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loadedBracketMatches, setLoadedBracketMatches] = useState<Record<number, { matches: BracketMatches }>>({});
  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);
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
    if (!id) return;
    const fetchData = async () => {
      setLoading(true);
      setError("");
      try {
        const bracketsData = await getTournamentBracketsById(Number(id));
        setBrackets(bracketsData);
        const tournamentData = await getTournamentById(Number(id));
        setTournament(tournamentData);
      } catch (error) {
        console.error("Error fetching tournament brackets:", error);
        setError(t("fetchError"));
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, t]);

  useEffect(() => {
    if (!brackets.length) return;
    const searchLower = (debouncedSearch ?? "").trim().toLowerCase();
    if (!searchLower) {
      setFilteredBrackets(brackets);
      return;
    }
    const result = brackets.filter((bracket) => {
      const matchesBracketCategory = bracket.category?.toLowerCase().includes(searchLower);
      const matchesDisplayName = bracket.display_name?.toLowerCase().includes(searchLower);
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

  if (!id) return null;

  return (
    <WebSocketProvider tournamentId={id as string}>
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
                    <DateRange start={tournament.start_date} end={tournament.end_date} />
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
        {error && <p className="text-red-500">{error}</p>}

        <Tabs
          value={selectedDay}
          onValueChange={(v) => {
            setSelectedDay(v);
            setOpenBracketIds([]);
          }}
        >
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
                          className="text-lg font-medium group flex items-center justify-between"
                          onClick={() => {
                            if (!loadedBracketMatches[bracket.id]) {
                              loadBracketData(bracket.id);
                            }
                          }}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                            <span className="text-base font-semibold">{bracket.display_name || bracket.category}</span>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <span>{(bracket.start_time && bracket.start_time.slice(0, 5)) || " — "}</span>
                              <span> | </span>
                              <span>
                                {t("participantsCount")}: {bracket.participants.length || " — "}
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
