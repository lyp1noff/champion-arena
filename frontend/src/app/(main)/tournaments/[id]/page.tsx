"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getTournamentBracketsById } from "@/lib/api/tournaments";
import { Bracket, BracketMatches } from "@/lib/interfaces";
import ScreenLoader from "@/components/loader";
import Link from "next/link";
import { LinkIcon } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { getBracketMatchesById } from "@/lib/api/brackets";
import BracketContent from "@/components/bracket-content";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function TournamentPage() {
  const { id } = useParams();
  const [tab, setTab] = useState("brackets");
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loadedBracketMatches, setLoadedBracketMatches] = useState<
    Record<number, { loading: boolean; matches: BracketMatches }>
  >({});

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
        const data = await getTournamentBracketsById(Number(id));
        setBrackets(data);
      } catch (error) {
        console.error("Error fetching tournament brackets:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  return (
    <div className="container py-10 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-10">Турнир #{id}</h1>

      <Tabs defaultValue="brackets" onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="brackets">Сетка</TabsTrigger>
          <TabsTrigger value="participants">Участники</TabsTrigger>
        </TabsList>
      </Tabs>

      {loading && <ScreenLoader fullscreen />}
      {error && <p className="text-red-500">{error}</p>}

      {brackets.length > 0 && (
        <Accordion type="multiple" className="w-full">
          {brackets.map((bracket) => (
            <AccordionItem key={bracket.id} value={String(bracket.id)}>
              <AccordionTrigger
                className="text-lg font-medium group flex items-center justify-between"
                onClick={() => {
                  if (!loadedBracketMatches[bracket.id]) {
                    loadBracketData(bracket.id);
                  }
                }}
              >
                {bracket.category}
              </AccordionTrigger>

              <AccordionContent>
                {tab === "brackets" ? (
                  loadedBracketMatches[bracket.id]?.loading ? (
                    <div className="flex items-center justify-center" style={{ height: 400 }}>
                      <ScreenLoader />
                    </div>
                  ) : (
                    <BracketContent
                      bracketMatches={loadedBracketMatches[bracket.id]?.matches ?? []}
                      matchCardHeight={60}
                      containerHeight={400}
                    />
                  )
                ) : (
                  <>
                    <Link
                      href={`/brackets/${bracket.id}`}
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <LinkIcon className="w-4 h-4" />
                    </Link>
                    <ul className="list-decimal list-inside mt-2">
                      {bracket.participants.map((p) => (
                        <li key={p.seed} className="py-1">
                          {p.last_name} {p.first_name}
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      )}

      {!loading && brackets.length === 0 && <p className="text-gray-500">Нет данных</p>}
    </div>
  );
}
