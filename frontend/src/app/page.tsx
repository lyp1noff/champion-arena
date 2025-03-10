import Image from "next/image";
import Link from "next/link";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { CalendarIcon, MapPinIcon } from "lucide-react";

export default function TournamentsPage() {
  // Sample tournament data - in a real app, this would come from an API or database
  const tournaments = [
    {
      id: 1,
      title: "Summer Championship",
      place: "Kyiv, Ukraine",
      date: "June 15-20, 2024",
      image: "/photo.jpg?height=200&width=400",
    },
    {
      id: 2,
      title: "Winter Classic",
      place: "Kyiv, Ukraine",
      date: "January 10-15, 2025",
      image: "/photo.jpg?height=200&width=400",
    },
    {
      id: 3,
      title: "Spring Tournament",
      place: "Kyiv, Ukraine",
      date: "April 5-10, 2024",
      image: "/photo.jpg?height=200&width=400",
    },
    {
      id: 4,
      title: "Fall Invitational",
      place: "Kyiv, Ukraine",
      date: "October 12-17, 2024",
      image: "/photo.jpg?height=200&width=400",
    },
    {
      id: 5,
      title: "Regional Qualifier",
      place: "Kyiv, Ukraine",
      date: "August 22-25, 2024",
      image: "/photo.jpg?height=200&width=400",
    },
    {
      id: 6,
      title: "National Championship",
      place: "Kyiv, Ukraine",
      date: "December 1-6, 2024",
      image: "/photo.jpg?height=200&width=400",
    },
  ];

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
                  src={tournament.image || "/placeholder.svg"}
                  alt={tournament.title}
                  fill
                  className="object-cover"
                  priority={tournament.id <= 3}
                />
              </div>
              <CardHeader>
                <h2 className="text-xl font-semibold">{tournament.title}</h2>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center text-sm text-muted-foreground">
                  <MapPinIcon className="mr-2 h-4 w-4" />
                  {tournament.place}
                </div>
                <div className="flex items-center text-sm text-muted-foreground">
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {tournament.date}
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
