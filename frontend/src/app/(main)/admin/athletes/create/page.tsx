"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createAthletes } from "@/lib/api/athletes";
import AthleteForm from "@/components/athlete-form";
import { AthleteCreate } from "@/lib/interfaces";

export default function CreateAthletePage() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const router = useRouter();

  async function handleCreate(values: AthleteCreate) {
    setIsSubmitting(true);
    await createAthletes(values);
    router.push("/admin/athletes");
    setIsSubmitting(false);
  }

  return (
    <div className="container py-10">
      <AthleteForm onSubmit={handleCreate} isSubmitting={isSubmitting} />
    </div>
  );
}
