"use client";

import ScreenLoader from "@/components/loader";
// import MatchCard from "@/components/match-card";
import { getBracketMatchesById } from "@/lib/api/brackets";
import { BracketMatches } from "@/lib/interfaces";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function BracketsPage() {
  const { id } = useParams();
  const [matches, setMatches] = useState<BracketMatches>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    const fetchData = async () => {
      setLoading(true);
      setError("");

      try {
        const data = await getBracketMatchesById(Number(id));
        setMatches(data);
      } catch (error) {
        console.error("Error fetching tournament matches:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  return (
    <div className="p-4">
      {loading && <ScreenLoader fullscreen={false} />}
      {error && <p className="text-red-500">{error}</p>}
      <h1 className="text-3xl font-bold py-4">👋 Чистый холст для Brackets {id}</h1>
      {matches && (
        <p>{matches[0].id}</p>
        // <div className="py-4">
        //   {matches.map((match) => (
        //     <h3 className="text-lg font-medium border-b pb-1 group-hover:text-primary transition-colors select-none">
        //       {match.id}
        //     </h3>
        //   ))}
        // </div>
        // <div className="flex items-start gap-10">
        //   <div className="flex flex-col gap-10">
        //     <MatchCard match={matches[0]} />
        //     <MatchCard match={matches[1]} />
        //   </div>

        //   <div className="flex flex-col">
        //     <div className="h-[50%]"></div> {/* чтобы матч встал между двумя */}
        //     <MatchCard match={matches[2]} />
        //   </div>
        // </div>
      )}

      {!loading && !matches && <p className="text-gray-500">Нет данных</p>}
    </div>
  );
}
