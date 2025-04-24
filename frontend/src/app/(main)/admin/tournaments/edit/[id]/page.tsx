"use client";

import { useParams, useRouter } from "next/navigation";
import { TournamentForm } from "@/components/tournament-form";

export default function EditTournamentPage() {
  const router = useRouter();
  const { id } = useParams();

  return (
    <div className="container py-10">
      <TournamentForm
        mode="edit"
        tournamentId={Number(id)}
        onSuccess={() => {
          router.push("/admin/tournaments");
        }}
      />
    </div>
  );
}
