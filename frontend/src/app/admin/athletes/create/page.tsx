"use client";

import { useRouter } from "next/navigation";
import { createAthlete } from "@/lib/api/athletes";
import AthleteForm from "@/components/athlete-form";
import { AthleteCreate } from "@/lib/interfaces";

import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { toast } from "sonner";

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
