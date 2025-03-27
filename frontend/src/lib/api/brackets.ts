import { Bracket, BracketMatches } from "../interfaces";

const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getBracketsById(id: number): Promise<Bracket> {
  const res = await fetch(`${url}/brackets/${id}`, { cache: "no-store", credentials: "include" });

  if (!res.ok) {
    throw new Error("Failed to load bracket");
  }

  return res.json();
}

export async function getBracketMatchesById(id: number): Promise<BracketMatches> {
  const res = await fetch(`${url}/brackets/${id}/matches`, { cache: "no-store", credentials: "include" });

  if (!res.ok) {
    throw new Error("Failed to load bracket");
  }

  return res.json();
}
