"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getTournamentBracketsById } from "@/lib/api/tournaments";
import { Bracket } from "@/lib/interfaces";
import ScreenLoader from "@/components/loader";
import Link from "next/link";
import { LinkIcon } from "lucide-react";

export default function TournamentPage() {
  const { id } = useParams();
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

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

  const toggle = (id: number) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="container py-10 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Турнир #{id}</h1>

      {loading && <ScreenLoader fullscreen={false} />}
      {error && <p className="text-red-500">{error}</p>}

      {brackets.length > 0 && (
        <div className="py-4">
          {brackets.map((bracket) => (
            <div key={bracket.id} className="mb-4">
              <div className="flex items-center gap-2 cursor-pointer group" onClick={() => toggle(bracket.id)}>
                <h3 className="text-lg font-medium border-b pb-1 group-hover:text-primary transition-colors select-none">
                  {bracket.category}
                </h3>
                <Link
                  href={`/brackets/${bracket.id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="text-muted-foreground hover:text-primary"
                >
                  <LinkIcon className="w-4 h-4" />
                </Link>
              </div>

              <div
                className={`overflow-hidden transition-all duration-150 ease-in-out ${
                  expanded[bracket.id] ? "max-h-96 opacity-100" : "max-h-0 opacity-0"
                }`}
              >
                <ul className="list-decimal pl-5 mt-2">
                  {bracket.participants.map((p) => (
                    <li key={p.seed} className="py-1">
                      {p.last_name} {p.first_name}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && brackets.length === 0 && <p className="text-gray-500">Нет данных</p>}
    </div>
  );
}
