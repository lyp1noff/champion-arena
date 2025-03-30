"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { getTournamentBracketsById } from "@/lib/api/tournaments";
import { Bracket } from "@/lib/interfaces";
import ScreenLoader from "@/components/loader";
import Link from "next/link";
import { LinkIcon } from "lucide-react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";

export default function TournamentPage() {
  const { id } = useParams();
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [loading, setLoading] = useState(true);
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
        <Accordion type="multiple" className="w-full">
          {brackets.map((bracket) => (
            <AccordionItem key={bracket.id} value={String(bracket.id)}>
              <AccordionTrigger className="text-lg font-medium group flex items-center justify-between">
                {bracket.category}
              </AccordionTrigger>

              <AccordionContent>
                <Link href={`/brackets/${bracket.id}`} rel="noopener noreferrer" onClick={(e) => e.stopPropagation()}>
                  <LinkIcon className="w-4 h-4" />
                </Link>
                <ul className="list-decimal list-inside mt-2">
                  {bracket.participants.map((p) => (
                    <li key={p.seed} className="py-1">
                      {p.last_name} {p.first_name}
                    </li>
                  ))}
                </ul>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      )}

      {!loading && brackets.length === 0 && <p className="text-gray-500">Нет данных</p>}
    </div>
  );
}
