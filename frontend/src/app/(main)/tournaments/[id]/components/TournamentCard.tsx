import { Card, CardContent } from "@/components/ui/card";
import { DateRange } from "@/components/date-range";
import { getLocale, getTranslations } from "next-intl/server";
import { CalendarDays, MapPin, Trophy, Users } from "lucide-react";
import { Tournament } from "@/lib/interfaces";
import Image from "next/image";

const cdnUrl = process.env.NEXT_PUBLIC_CDN_URL;

interface TournamentCardProps {
  tournament: Tournament;
  uniqueParticipantsCount: number;
  categoriesCount: number;
}

export default async function TournamentCard({
  tournament,
  uniqueParticipantsCount,
  categoriesCount,
}: TournamentCardProps) {
  const locale = await getLocale();
  const t = await getTranslations("TournamentPage");

  return (
    <Card className="mb-10 shadow-lg rounded-2xl overflow-hidden">
      <CardContent className="p-0 flex flex-col sm:flex-row">
        <div className="relative w-full h-auto sm:w-64 sm:h-64 bg-muted flex items-center justify-center">
          <Image
            src={tournament.image_url ? `${cdnUrl}/${tournament.image_url}` : "/tournament.svg"}
            alt={tournament.name}
            width={500}
            height={500}
            className="object-contain w-full h-auto sm:w-64 sm:h-64 sm:object-cover"
          />
        </div>

        <div className="p-6 flex flex-col justify-center gap-3 text-base">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-muted-foreground" />
            <span>{tournament.location || t("unknownLocation")}</span>
          </div>

          <div className="flex items-center gap-2">
            <CalendarDays className="w-5 h-5 text-muted-foreground" />
            <span>
              <DateRange start={tournament.start_date} end={tournament.end_date} locale={locale} />
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-muted-foreground" />
            <span>
              {t("categoriesCount")}: {categoriesCount}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-muted-foreground" />
            <span>
              {t("participantsCount")}: {uniqueParticipantsCount}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
