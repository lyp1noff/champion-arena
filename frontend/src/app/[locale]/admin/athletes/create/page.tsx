"use client";

import { useRouter } from "@/i18n/navigation";
import { toast } from "sonner";

import AthleteForm from "@/components/athlete-form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { createAthlete } from "@/lib/api/athletes";
import { AthleteCreate } from "@/lib/interfaces";

export default function CreateAthletePage() {
  const router = useRouter();

  async function handleCreate(values: AthleteCreate) {
    try {
      await createAthlete(values);
      toast.success("Athlete created successfully");
      router.push("/admin/athletes");
    } catch {
      toast.error("Failed to create athlete");
    }
  }

  return (
    <div className="container py-10 max-w-2xl">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Add New Athlete</CardTitle>
        </CardHeader>
        <CardContent>
          <AthleteForm onSuccess={handleCreate} />
        </CardContent>
      </Card>
    </div>
  );
}
