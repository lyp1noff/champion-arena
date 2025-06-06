import { Application, ApplicationResponse } from "@/lib/interfaces";

const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getApplications(tournamentId: number) {
  const res = await fetch(`${url}/tournaments/${tournamentId}/applications`, {
    credentials: "include",
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to load applications");
  return res.json();
}

export async function createApplication(data: Application): Promise<ApplicationResponse> {
  const res = await fetch(`${url}/tournaments/${data.tournament_id}/applications`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
    credentials: "include",
  });

  if (!res.ok) {
    const msg = (await res.json())?.detail || "Failed to submit";
    throw new Error(msg);
  }

  return res.json();
}
