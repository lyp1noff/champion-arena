import { notFound } from "next/navigation";

import TournamentBrackets from "@/app/(main)/tournaments/[id]/components/TournamentBrackets";
import TournamentCard from "@/app/(main)/tournaments/[id]/components/TournamentCard";

import { getTournamentBracketsById, getTournamentById } from "@/lib/api/tournaments";

export default async function TournamentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  const [tournament, brackets] = await Promise.all([
    getTournamentById(Number(id)).catch(() => null),
    getTournamentBracketsById(Number(id)).catch(() => []),
  ]);

  if (!tournament) {
    notFound();
  }

  const uniqueParticipantsCount = new Set(brackets.flatMap((b) => b.participants.map((p) => p.athlete_id))).size;

  return (
    <div className="container py-10 mx-auto">
      <h1 className="text-2xl font-bold mb-10">{tournament.name}</h1>
      <TournamentCard
        tournament={tournament}
        uniqueParticipantsCount={uniqueParticipantsCount}
        categoriesCount={brackets.length}
      />
      <TournamentBrackets tournament={tournament} brackets={brackets} />
    </div>
  );
}
