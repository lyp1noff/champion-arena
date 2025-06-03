"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getTournamentBracketsById, getTournamentById } from "@/lib/api/tournaments";
import { Bracket, BracketMatches, Tournament } from "@/lib/interfaces";
import ScreenLoader from "@/components/loader";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { getBracketMatchesById } from "@/lib/api/brackets";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
// import { useScreenHeight } from "@/hooks/use-screen-height";
import { useTranslations } from "next-intl";
import { BracketView } from "@/components/bracket_view";
import { ParticipantsView } from "@/components/participants_view";
import { Input } from "@/components/ui/input";
import { useDebounce } from "use-debounce";

export default function TournamentPage() {
  const t = useTranslations("TournamentPage");

  const { id } = useParams();
  const [tab, setTab] = useState("brackets");
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [tournament, setTournament] = useState<Tournament>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loadedBracketMatches, setLoadedBracketMatches] = useState<
    Record<number, { loading: boolean; matches: BracketMatches }>
  >({});

  const [search, setSearch] = useState("");
  const [debouncedSearch] = useDebounce(search, 500);
  const [filteredBrackets, setFilteredBrackets] = useState<Bracket[]>([]);
  // const [searchFields, setSearchFields] = useState({
  //   bracketCategory: true,
  //   participantFirstName: true,
  //   participantLastName: true,
  //   coachLastName: true,
  // });

  // const screenHeight = useScreenHeight();
  // const maxHeight = screenHeight * 0.7;
  // const matchCardHeight = 60;

  const loadBracketData = async (bracketId: number) => {
    if (loadedBracketMatches[bracketId]) return;

    setLoadedBracketMatches((prev) => ({
      ...prev,
      [bracketId]: { loading: true, matches: [] },
    }));

    try {
      const res = await getBracketMatchesById(bracketId);
      setLoadedBracketMatches((prev) => ({
        ...prev,
        [bracketId]: { loading: false, matches: res },
      }));
    } catch (err) {
      console.error("Error fetching tournament bracketMatches:", err);
      setLoadedBracketMatches((prev) => ({
        ...prev,
        [bracketId]: { loading: false, matches: [] },
      }));
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
        setTournament(tournamentData); // separate two api calls
      } catch (error) {
        console.error("Error fetching tournament brackets:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  useEffect(() => {
    if (!brackets.length) return;

    const searchLower = (debouncedSearch ?? "").trim().toLowerCase();

    if (!searchLower) {
      setFilteredBrackets(brackets);
      return;
    }

    const result = brackets.filter((bracket) => {
      const matchesBracketCategory = bracket.category?.toLowerCase().includes(searchLower);

      const matchesParticipant = bracket.participants.some((participant) => {
        const firstName = participant.first_name?.toLowerCase() ?? "";
        const lastName = participant.last_name?.toLowerCase() ?? "";
        const coachLastName = participant.coach_last_name?.toLowerCase() ?? "";

        return firstName.includes(searchLower) || lastName.includes(searchLower) || coachLastName.includes(searchLower);
      });

      return matchesBracketCategory || matchesParticipant;
    });

    setFilteredBrackets(result);
  }, [debouncedSearch, brackets]);

  const bracketsByTatami = filteredBrackets.reduce<Record<string, typeof brackets>>((acc, bracket) => {
    const tatamiKey = bracket.tatami ?? "Unknown";
    if (!acc[tatamiKey]) {
      acc[tatamiKey] = [];
    }
    acc[tatamiKey].push(bracket);
    return acc;
  }, {});

  return (
    <div className="container py-10 mx-auto">
      <h1 className="text-2xl font-bold mb-10">{tournament ? tournament.name : "Tournament"}</h1>

      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6 sm:mb-10">
        <Input
          placeholder={"Search brackets or participants..."}
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value)}
        />

        <Tabs defaultValue="brackets" onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="brackets">{t("brackets")}</TabsTrigger>
            <TabsTrigger value="participants">{t("participants")}</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {loading && <ScreenLoader fullscreen />}
      {error && <p className="text-red-500">{error}</p>}

      {Object.entries(bracketsByTatami).map(([tatami, tatamiBrackets]) => (
        <div key={tatami} className="mt-10">
          <h2 className="text-2xl font-bold mb-2">Tatami {tatami}</h2>
          <Accordion type="multiple" className="w-full">
            {tatamiBrackets.map((bracket) => {
              // const { cardHeight, roundTitleHeight, columnGap } = getBracketDimensions(matchCardHeight);
              // const estimatedHeight =
              //   getInitialMatchCount(bracket.participants.length) * (cardHeight + columnGap) + roundTitleHeight;
              // const containerHeight = estimatedHeight > maxHeight ? maxHeight : estimatedHeight;

              return (
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
                      <span className="text-base font-semibold">{bracket.category}</span>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        {/* i18n needed*/}
                        <span>{bracket.start_time.slice(0, 5) || " — "}</span>
                        <span> | </span>
                        <span>Participants: {bracket.participants.length || " — "}</span>
                      </div>
                    </div>
                  </AccordionTrigger>

                  <AccordionContent>
                    {tab !== "brackets" ? (
                      <ParticipantsView bracket={bracket} />
                    ) : (
                      <BracketView
                        loading={loadedBracketMatches[bracket.id]?.loading ?? true}
                        matches={loadedBracketMatches[bracket.id]?.matches ?? []}
                        bracket={bracket}
                        // maxHeight={maxHeight}
                      />
                    )}
                  </AccordionContent>
                </AccordionItem>
              );
            })}
          </Accordion>
        </div>
      ))}

      {!loading && brackets.length === 0 && <p className="text-gray-500">No Data</p>}
    </div>
  );
}
