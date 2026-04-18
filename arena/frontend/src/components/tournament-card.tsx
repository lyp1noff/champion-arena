"use client";

import Image from "next/image";

import { CalendarDays, FileUser, MapPin, Trophy, Users } from "lucide-react";

import { DateRange } from "@/components/date-range";
import { Card, CardContent } from "@/components/ui/card";

import { CDN_URL } from "@/lib/config";
import { Tournament } from "@/lib/interfaces";

interface TournamentCardProps {
  tournament: Tournament | null;
  locale: string;
  unknownLocation: string;
  applicationsCount: string;
  participantsCount: string;
  categoriesCount: string;
}

export default function TournamentCard({
  tournament,
  locale,
  unknownLocation,
  applicationsCount,
  participantsCount,
  categoriesCount,
}: TournamentCardProps) {
  return (
    <Card className="mb-10 shadow-lg rounded-2xl overflow-hidden">
      <CardContent className="p-0 flex flex-col sm:flex-row">
        <div className="relative w-full h-auto sm:w-64 sm:h-64 bg-muted flex items-center justify-center">
          <Image
            src={tournament?.image_url ? `${CDN_URL}/${tournament.image_url}` : "/tournament.svg"}
            alt={tournament?.name || "Tournament"}
            width={500}
            height={500}
            className="object-contain w-full h-auto sm:w-64 sm:h-64 sm:object-cover"
          />
        </div>

        <div className="p-6 flex flex-col justify-center gap-3 text-base">
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-muted-foreground" />
            <span>{tournament?.location || unknownLocation}</span>
          </div>

          <div className="flex items-center gap-2">
            <CalendarDays className="w-5 h-5 text-muted-foreground" />
            <span>
              {tournament ? (
                <DateRange start={tournament.start_date} end={tournament.end_date} locale={locale} />
              ) : (
                "--"
              )}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <FileUser className="w-5 h-5 text-muted-foreground" />
            <span>{applicationsCount}</span>
          </div>

          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-muted-foreground" />
            <span>{participantsCount}</span>
          </div>

          <div className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-muted-foreground" />
            <span>{categoriesCount}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
