"use client";

import { useEffect, useMemo, useState } from "react";

import { useLocale, useTranslations } from "next-intl";
import Link from "next/link";
import { useParams } from "next/navigation";

import TournamentCard from "@/components/tournament-card";
import { TournamentForm } from "@/components/tournament-form";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";

import { getTournamentBracketsById, getTournamentById } from "@/lib/api/tournaments";
import { Bracket, Tournament } from "@/lib/interfaces";

export default function TournamentAdminPage() {
  const t = useTranslations("AdminTournaments");
  const tPublic = useTranslations("TournamentPage");
  const locale = useLocale();
  const params = useParams();
  const tournamentId = Number(params?.id);

  const [tournament, setTournament] = useState<Tournament | null>(null);
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [isEditOpen, setIsEditOpen] = useState(false);

  useEffect(() => {
    if (!tournamentId) return;
    Promise.all([getTournamentById(tournamentId), getTournamentBracketsById(tournamentId)])
      .then(([tournamentData, bracketsData]) => {
        setTournament(tournamentData);
        setBrackets(bracketsData);
      })
      .catch(() => null);
  }, [tournamentId]);

  const stats = useMemo(() => {
    const uniqueIds = new Set<number>();
    const participantsCount = brackets.reduce((acc, b) => {
      for (const p of b.participants) uniqueIds.add(p.athlete_id);
      return acc + b.participants.length;
    }, 0);
    return {
      participantsCount,
      uniqueParticipantsCount: uniqueIds.size,
      categoriesCount: brackets.length,
    };
  }, [brackets]);

  if (!tournamentId) return null;

  return (
    <div className="container h-full flex-1 flex-col gap-8 p-8 md:flex">
      <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-4">
          <TournamentCard
            tournament={tournament}
            locale={locale}
            unknownLocation={tPublic("unknownLocation")}
            applicationsCount={tPublic("applicationsCount", { count: stats.participantsCount })}
            participantsCount={tPublic("participantsCount", { count: stats.uniqueParticipantsCount })}
            categoriesCount={tPublic("categoriesCount", { count: stats.categoriesCount })}
          />

          <div className="flex flex-wrap gap-2">
            <Link href={`/tournaments/${tournamentId}`}>
              <Button variant="outline">{t("publicPage")}</Button>
            </Link>
            <Button variant="outline" onClick={() => setIsEditOpen(true)}>
              {t("edit")}
            </Button>
          </div>
        </div>

        <Card className="h-fit">
          <CardHeader>
            <CardTitle>{t("adminHubTitle")}</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            <Link href={`/admin/tournaments/${tournamentId}/manage`}>
              <Button className="w-full" variant="outline">
                {t("manage")}
              </Button>
            </Link>
            <Link href={`/admin/tournaments/${tournamentId}/applications`}>
              <Button className="w-full" variant="outline">
                {t("applications")}
              </Button>
            </Link>
            <Link href={`/admin/tournaments/${tournamentId}/reports`}>
              <Button className="w-full" variant="outline">
                {t("reports")}
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
        <DialogContent className="max-w-3xl">
          <DialogTitle>{t("edit")}</DialogTitle>
          {tournament && (
            <TournamentForm
              tournamentId={tournament.id}
              onSuccess={() => {
                setIsEditOpen(false);
                getTournamentById(tournament.id)
                  .then(setTournament)
                  .catch(() => null);
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
