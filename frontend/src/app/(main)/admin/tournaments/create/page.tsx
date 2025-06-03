"use client";

import { useRouter } from "next/navigation";
import { TournamentForm } from "@/components/tournament-form";

export default function CreateTournamentPage() {
  const router = useRouter();

  return (
    <div className="container py-10">
      <TournamentForm
        mode="create"
        onSuccess={() => {
          router.push("/admin/tournaments");
        }}
      />
    </div>
  );
}
