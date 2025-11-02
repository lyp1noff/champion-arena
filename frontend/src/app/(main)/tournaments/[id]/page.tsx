import TournamentPageContent from "./components/TournamentPageContent";
import { getTournamentById, getTournamentBracketsById } from "@/lib/api/tournaments";

export default async function TournamentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  const [tournament, brackets] = await Promise.all([
    getTournamentById(Number(id)).catch(() => null),
    getTournamentBracketsById(Number(id)).catch(() => []),
  ]);

  return <TournamentPageContent tournament={tournament} brackets={brackets} />;
}
