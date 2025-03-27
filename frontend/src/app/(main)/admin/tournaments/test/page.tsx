"use client";

import { useState } from "react";
import Link from "next/link";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Edit, Trash2, Plus, Search, CalendarIcon, MapPinIcon, ArrowUpDown } from "lucide-react";
import { Input } from "@/components/ui/input";

export default function AdminTournamentsPage() {
  const initialTournaments = [
    {
      id: 1,
      title: "Summer Championship",
      place: "Los Angeles, CA",
      date: "June 15-20, 2024",
      status: "Upcoming",
      participants: 32,
      createdAt: "2024-01-15",
    },
    {
      id: 2,
      title: "Winter Classic",
      place: "Denver, CO",
      date: "January 10-15, 2025",
      status: "Draft",
      participants: 24,
      createdAt: "2024-02-20",
    },
    {
      id: 3,
      title: "Spring Tournament",
      place: "Miami, FL",
      date: "April 5-10, 2024",
      status: "Active",
      participants: 16,
      createdAt: "2023-11-05",
    },
    {
      id: 4,
      title: "Fall Invitational",
      place: "Chicago, IL",
      date: "October 12-17, 2024",
      status: "Upcoming",
      participants: 48,
      createdAt: "2024-03-01",
    },
    {
      id: 5,
      title: "Regional Qualifier",
      place: "Seattle, WA",
      date: "August 22-25, 2024",
      status: "Upcoming",
      participants: 64,
      createdAt: "2024-02-10",
    },
    {
      id: 6,
      title: "National Championship",
      place: "New York, NY",
      date: "December 1-6, 2024",
      status: "Draft",
      participants: 128,
      createdAt: "2024-01-30",
    },
    {
      id: 7,
      title: "International Open",
      place: "Toronto, Canada",
      date: "July 8-14, 2024",
      status: "Upcoming",
      participants: 96,
      createdAt: "2024-02-15",
    },
    {
      id: 8,
      title: "City League Finals",
      place: "Boston, MA",
      date: "September 5-7, 2024",
      status: "Draft",
      participants: 16,
      createdAt: "2024-03-10",
    },
    {
      id: 9,
      title: "Youth Championship",
      place: "Orlando, FL",
      date: "May 20-22, 2024",
      status: "Active",
      participants: 32,
      createdAt: "2023-12-12",
    },
    {
      id: 10,
      title: "Veterans Tournament",
      place: "San Diego, CA",
      date: "November 11-13, 2024",
      status: "Upcoming",
      participants: 24,
      createdAt: "2024-01-20",
    },
    {
      id: 11,
      title: "College Showcase",
      place: "Austin, TX",
      date: "March 15-18, 2025",
      status: "Draft",
      participants: 48,
      createdAt: "2024-02-28",
    },
    {
      id: 12,
      title: "Pro-Am Challenge",
      place: "Las Vegas, NV",
      date: "February 5-9, 2025",
      status: "Draft",
      participants: 32,
      createdAt: "2024-03-05",
    },
  ];

  const [tournaments, setTournaments] = useState(initialTournaments);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");

  // Filter tournaments based on search query
  const filteredTournaments = tournaments.filter(
    (tournament) =>
      tournament.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tournament.place.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Handle sorting
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // Sort tournaments
  const sortedTournaments = [...filteredTournaments].sort((a, b) => {
    if (!sortField) return 0;

    const fieldA = a[sortField as keyof typeof a];
    const fieldB = b[sortField as keyof typeof b];

    if (typeof fieldA === "string" && typeof fieldB === "string") {
      return sortDirection === "asc" ? fieldA.localeCompare(fieldB) : fieldB.localeCompare(fieldA);
    }

    return sortDirection === "asc" ? Number(fieldA) - Number(fieldB) : Number(fieldB) - Number(fieldA);
  });

  // Handle delete (placeholder)
  const handleDelete = (id: number) => {
    if (confirm("Are you sure you want to delete this tournament?")) {
      setTournaments(tournaments.filter((t) => t.id !== id));
    }
  };

  return (
    <div className="container py-10">
      <Card>
        <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <CardTitle className="text-2xl">Tournaments Management</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">Manage all tournaments in the system</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto">
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search tournaments..."
                className="pl-8 w-full"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <Button className="w-full sm:w-auto">
              <Plus className="mr-2 h-4 w-4" /> Add Tournament
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px] rounded-md border">
            <div className="w-full min-w-[800px]">
              <div className="grid grid-cols-[1fr_1fr_150px_100px_100px_120px] bg-muted px-4 py-3 sticky top-0 border-b">
                <button className="flex items-center text-sm font-medium" onClick={() => handleSort("title")}>
                  Title
                  <ArrowUpDown className="ml-2 h-4 w-4" />
                </button>
                <button className="flex items-center text-sm font-medium" onClick={() => handleSort("place")}>
                  Location
                  <ArrowUpDown className="ml-2 h-4 w-4" />
                </button>
                <button className="flex items-center text-sm font-medium" onClick={() => handleSort("date")}>
                  Date
                  <ArrowUpDown className="ml-2 h-4 w-4" />
                </button>
                <button className="flex items-center text-sm font-medium" onClick={() => handleSort("status")}>
                  Status
                  <ArrowUpDown className="ml-2 h-4 w-4" />
                </button>
                <button className="flex items-center text-sm font-medium" onClick={() => handleSort("participants")}>
                  Participants
                  <ArrowUpDown className="ml-2 h-4 w-4" />
                </button>
                <div className="text-sm font-medium text-right">Actions</div>
              </div>

              {sortedTournaments.length > 0 ? (
                sortedTournaments.map((tournament) => (
                  <div
                    key={tournament.id}
                    className="grid grid-cols-[1fr_1fr_150px_100px_100px_120px] px-4 py-4 border-b items-center hover:bg-muted/50"
                  >
                    <div className="font-medium">{tournament.title}</div>
                    <div className="flex items-center text-sm">
                      <MapPinIcon className="mr-2 h-4 w-4 text-muted-foreground" />
                      {tournament.place}
                    </div>
                    <div className="flex items-center text-sm">
                      <CalendarIcon className="mr-2 h-4 w-4 text-muted-foreground" />
                      {tournament.date}
                    </div>
                    <div>
                      <span
                        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                          tournament.status === "Active"
                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
                            : tournament.status === "Upcoming"
                            ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300"
                            : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300"
                        }`}
                      >
                        {tournament.status}
                      </span>
                    </div>
                    <div className="text-sm">{tournament.participants}</div>
                    <div className="flex justify-end gap-2">
                      <Button variant="outline" size="icon" asChild>
                        <Link href={`/admin/tournaments/${tournament.id}/edit`}>
                          <Edit className="h-4 w-4" />
                          <span className="sr-only">Edit</span>
                        </Link>
                      </Button>
                      <Button
                        variant="outline"
                        size="icon"
                        className="text-destructive hover:bg-destructive/10"
                        onClick={() => handleDelete(tournament.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                        <span className="sr-only">Delete</span>
                      </Button>
                    </div>
                  </div>
                ))
              ) : (
                <div className="px-4 py-8 text-center text-muted-foreground">
                  No tournaments found. Try adjusting your search.
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
