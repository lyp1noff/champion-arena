"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ScreenLoader from "@/components/loader";
import MatchCard from "@/components/match-card";
import { BracketMatch } from "@/lib/interfaces";
import { getBracketMatchesById } from "@/lib/api/brackets";

export default function BracketPage() {
  const { id } = useParams();
  const [matches, setMatches] = useState<BracketMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    const fetchMatches = async () => {
      try {
        setLoading(true);
        const data = await getBracketMatchesById(Number(id));
        setMatches(data);
      } catch (err) {
        console.error(err);
        setError("Error fetching tournament matches");
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, [id]);

  if (loading) return <ScreenLoader />;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!matches.length) return <p className="text-gray-500">Нет данных</p>;

  const groupedRounds = matches.reduce((acc, match) => {
    if (!acc[match.round_number]) acc[match.round_number] = [];
    acc[match.round_number].push(match);
    return acc;
  }, {} as Record<number, BracketMatch[]>);

  const sortedRounds = Object.entries(groupedRounds)
    .map(([roundStr, matches]) => ({
      round: Number(roundStr),
      matches: matches.sort((a, b) => a.position - b.position),
    }))
    .sort((a, b) => a.round - b.round);

  return (
    <div className="p-10 overflow-x-auto">
      <h1 className="text-3xl font-bold mb-6">🏆 Сетка турнира #{id}</h1>

      <div className="flex gap-8 items-start">
        {sortedRounds.map(({ round, matches }) => (
          <ul key={round} className="flex flex-col items-center gap-8 min-w-[220px]">
            <h2 className="text-lg font-semibold mb-2">Раунд {round}</h2>
            {matches.map((match, matchIdx) => (
              <li key={match.id || `empty-${round}-${matchIdx}`} className="w-[220px]">
                {match.athlete1 || match.athlete2 ? (
                  <MatchCard match={match} />
                ) : (
                  <div className="w-full h-20 border border-dashed border-gray-300 rounded-md opacity-30" />
                )}
              </li>
            ))}
          </ul>
        ))}
      </div>
    </div>
  );
}
