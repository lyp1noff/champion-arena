"use client";

import { useEffect, useState } from "react";

import { useParams } from "next/navigation";

import { toast } from "sonner";

import { getCoaches } from "@/lib/api/api";
import { getAllAthletes } from "@/lib/api/athletes";
import { getCategories } from "@/lib/api/categories";
import { Athlete, Category, Coach } from "@/lib/interfaces";

import SubmitApplication from "./components/submit-application";

export default function Page() {
  const params = useParams();
  const tournamentId = Number(params?.id);

  const [coaches, setCoaches] = useState<Coach[]>([]);
  const [athletes, setAthletes] = useState<Athlete[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getCoaches(), getAllAthletes(), getCategories()])
      .then(([coaches, athletes, categories]) => {
        setCoaches(coaches);
        setAthletes(athletes);
        setCategories(categories);
      })
      .catch(() => toast.error("Failed to load application data"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-muted-foreground">Loading...</p>;

  return (
    <div className="container py-6">
      <SubmitApplication tournamentId={tournamentId} coaches={coaches} athletes={athletes} categories={categories} />
    </div>
  );
}
