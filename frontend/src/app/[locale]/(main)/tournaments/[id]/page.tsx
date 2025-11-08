import { notFound } from "next/navigation";

import TournamentBrackets from "@/app/[locale]/(main)/tournaments/[id]/components/TournamentBrackets";
import TournamentCard from "@/app/[locale]/(main)/tournaments/[id]/components/TournamentCard";

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

  const uniqueIds = new Set<number>();
  const participantsCount = brackets.reduce((acc, b) => {
    for (const p of b.participants) uniqueIds.add(p.athlete_id);
    return acc + b.participants.length;
  }, 0);
  const uniqueParticipantsCount = uniqueIds.size;

  return (
    <div className="container py-10 mx-auto">
      <h1 className="text-2xl font-bold mb-10">{tournament.name}</h1>
      <TournamentCard
        tournament={tournament}
        uniqueParticipantsCount={uniqueParticipantsCount}
        categoriesCount={brackets.length}
        applicationsCount={participantsCount}
      />
      <TournamentBrackets tournament={tournament} brackets={brackets} />
    </div>
  );
}
