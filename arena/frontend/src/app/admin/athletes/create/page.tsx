"use client";

import { useRouter } from "next/navigation";

import AthleteForm from "@/components/athlete-form";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function CreateAthletePage() {
  const router = useRouter();

  async function handleCreate() {
    router.push("/admin/athletes");
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
