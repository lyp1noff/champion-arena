"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getTournamentBracketsById } from "@/lib/api/tournaments";
import { Bracket } from "@/lib/interfaces";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import ScreenLoader from "@/components/loader";

export default function TournamentPage() {
  const { id } = useParams();
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
      <h1 className="text-2xl font-bold mb-4">Турнир #{id}</h1>

      {loading && <ScreenLoader fullscreen={false} />}

      {error && <p className="text-red-500">{error}</p>}

      {brackets.length > 0 && (
        <Card className="w-full shadow-md">
          <CardContent>
            <h2 className="text-xl font-semibold mb-3">Сетки турнира</h2>
            <ScrollArea className="h-96 border rounded-lg p-3">
              {brackets.map((bracket, idx) => (
                <div key={idx} className="mb-4">
                  <h3 className="text-lg font-medium border-b pb-1">{bracket.category}</h3>
                  <ul className="list-decimal pl-5 mt-2">
                    {bracket.participants.map((p) => (
                      <li key={p.seed} className="py-1">
                        {p.last_name} {p.first_name}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {brackets.length === 0 && !loading && <p className="text-gray-500">Нет данных</p>}
    </div>
  );
}
