"use client";

import { useRouter } from "next/navigation";
import { TournamentForm } from "@/components/tournament-form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CreateTournamentPage() {
  const router = useRouter();

  return (
    <div className="container py-10 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Add New Tournament</CardTitle>
        </CardHeader>
        <CardContent>
          <TournamentForm
            onSuccess={() => {
              router.push("/admin/tournaments");
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}
