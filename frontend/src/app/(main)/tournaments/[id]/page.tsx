import { getLocale, getTranslations } from "next-intl/server";
import { notFound } from "next/navigation";

import TournamentBrackets from "@/app/(main)/tournaments/[id]/components/TournamentBrackets";

import TournamentCard from "@/components/tournament-card";

import { getTournamentBracketsById, getTournamentById, getTournamentTimetableById } from "@/lib/api/tournaments";

export default async function TournamentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const tournamentId = Number(id);

  const [tournament, brackets, timetableEntries] = await Promise.all([
    getTournamentById(tournamentId).catch(() => null),
    getTournamentBracketsById(tournamentId).catch(() => []),
    getTournamentTimetableById(tournamentId).catch(() => []),
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
  const locale = await getLocale();
  const t = await getTranslations("TournamentPage");

  return (
    <div className="container py-10 mx-auto">
      <h1 className="text-2xl font-bold mb-10">{tournament.name}</h1>
      <TournamentCard
        tournament={tournament}
        locale={locale}
        unknownLocation={t("unknownLocation")}
        applicationsCount={t("applicationsCount", { count: participantsCount })}
        participantsCount={t("participantsCount", { count: uniqueParticipantsCount })}
        categoriesCount={t("categoriesCount", { count: brackets.length })}
      />
      <TournamentBrackets tournament={tournament} brackets={brackets} timetableEntries={timetableEntries} />
    </div>
  );
}
