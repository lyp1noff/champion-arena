"use client";

import Image from "next/image";
import Link from "next/link";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { CalendarIcon, MapPinIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Tournament } from "@/lib/interfaces";
import { getTournaments } from "@/lib/api/tournaments";
import { toast } from "sonner";

const cdnUrl = process.env.NEXT_PUBLIC_CDN_URL;

export default function TournamentsPage() {
  const [tournaments, setTournaments] = useState<Tournament[]>([]);
  // const [isLoadingTournaments, setIsLoadingTournaments] = useState(true);

  useEffect(() => {
    const fetchTournaments = async () => {
      // setIsLoadingTournaments(true);
      try {
        const data = await getTournaments(1, 10, "start_date", "desc", "");
        setTournaments(data.data);
      } catch (error) {
        console.error("Error fetching tournaments:", error);
        toast.error("Failed to load tournaments", {
          description: "Please try again or contact support.",
        });
      } finally {
        // setIsLoadingTournaments(false);
      }
    };

    fetchTournaments();
  }, []);

  return (
    <div className="container py-10">
      <h1 className="text-black dark:text-white text-3xl font-bold mb-8">
        <span className="dark:text-blue-500">Champion </span>Karate
        <span className="dark:text-championYellow"> Club </span>tournaments
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {tournaments.map((tournament) => (
          <Link
            href={`/tournaments/${tournament.id}`}
            key={tournament.id}
            className="block transition-transform hover:scale-[1.02]"
          >
            <Card className="h-full overflow-hidden">
              <div className="relative h-48 w-full">
                <Image
                  src={`${cdnUrl}/${tournament.image_url}` || "/tournament.svg"}
                  alt={tournament.name}
                  fill
                  className="object-cover"
                  priority={tournament.id <= 3}
                />
              </div>
              <CardHeader>
                <h2 className="text-xl font-semibold">{tournament.name}</h2>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center text-sm text-muted-foreground">
                  <MapPinIcon className="mr-2 h-4 w-4" />
                  {tournament.location}
                </div>
                <div className="flex items-center text-sm text-muted-foreground">
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {tournament.start_date.toLocaleString()}
                </div>
              </CardContent>
              <CardFooter>
                <div className="text-sm font-medium text-primary">View details</div>
              </CardFooter>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
