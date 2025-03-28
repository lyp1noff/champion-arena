"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import ScreenLoader from "@/components/loader";
import MatchCard from "@/components/match-card";
import { BracketMatch } from "@/lib/interfaces";
import { getBracketMatchesById } from "@/lib/api/brackets";

export default function BracketPage() {
  const { id } = useParams();
  const [bracketMatches, setMatches] = useState<BracketMatch[]>([]);
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
        setError("Ошибка загрузки матчей");
      } finally {
        setLoading(false);
      }
    };

    fetchMatches();
  }, [id]);

  if (loading) return <ScreenLoader />;
  if (error) return <p className="text-red-500">{error}</p>;
  if (!bracketMatches.length) return <p className="text-gray-500">Нет данных</p>;

  const groupedRounds = bracketMatches.reduce((acc, bracketMatch) => {
    if (!acc[bracketMatch.round_number]) acc[bracketMatch.round_number] = [];
    acc[bracketMatch.round_number].push(bracketMatch);
    return acc;
  }, {} as Record<number, BracketMatch[]>);

  const sortedRounds = Object.entries(groupedRounds)
    .map(([roundStr, bracketMatches]) => ({
      round: Number(roundStr),
      bracketMatches: bracketMatches.sort((a, b) => a.position - b.position),
    }))
    .sort((a, b) => a.round - b.round);

  return (
    <div className="p-10 overflow-x-auto">
      <h1 className="text-3xl font-bold mb-6">🏆 Сетка турнира #{id}</h1>

      <div className="flex gap-8 items-start">
        {sortedRounds.map(({ round, bracketMatches }) => {
          const firstWithLabel = bracketMatches.find((bm) => bm.match?.round_type);
          const title = firstWithLabel?.match.round_type ? firstWithLabel.match.round_type : `Раунд ${round}`;

          return (
            <ul key={round} className="flex flex-col items-center gap-8 min-w-[220px]">
              <h2 className="text-lg font-semibold mb-2">{title}</h2>
              {bracketMatches.map((bracketMatch, bracketMatchIdx) => (
                <li key={bracketMatch.id || `empty-${round}-${bracketMatchIdx}`} className="w-[220px]">
                  {bracketMatch.match.athlete1 || bracketMatch.match.athlete2 ? (
                    <MatchCard bracketMatch={bracketMatch} />
                  ) : (
                    <div className="w-full h-20 border border-dashed border-gray-300 rounded-md opacity-30" />
                  )}
                </li>
              ))}
            </ul>
          );
        })}
      </div>
    </div>
  );
}
