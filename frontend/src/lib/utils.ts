import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { BracketMatchAthlete, BracketMatches } from "@/lib/interfaces";

export const isServer = typeof window === "undefined";
export const isClient = !isServer;

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateToISO(date: Date): string {
  if (!date) throw new Error("Date is missing");
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatTimeToISO(timeStr: string | null | undefined): string | null {
  if (!timeStr) return null;

  const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)(:[0-5]\d)?$/;
  if (!timeRegex.test(timeStr)) {
    console.warn(`Invalid time format: ${timeStr}`);
    return null;
  }

  return timeStr.length === 5 ? `${timeStr}:00` : timeStr;
}

export function getInitialMatchCount(participantCount: number): number {
  const half = participantCount / 2;
  return 2 ** Math.ceil(Math.log2(half));
}

export function getBracketDimensions(matchCardHeight: number, matchCardWidth?: number) {
  const cardHeight = matchCardHeight;
  const cardWidth = matchCardWidth ?? cardHeight * 4;
  const roundTitleHeight = cardHeight / 3;
  const columnGap = (cardHeight / 8) * 2;
  const rowGap = cardHeight / 2.5;

  return { cardHeight, cardWidth, roundTitleHeight, columnGap, rowGap };
}

export function getUniqueAthletes(matches: BracketMatches): BracketMatchAthlete[] {
  const athleteMap = new Map<number, BracketMatchAthlete>();
  for (const match of matches) {
    const a1 = match.match.athlete1;
    const a2 = match.match.athlete2;
    if (a1) athleteMap.set(a1.id, a1);
    if (a2) athleteMap.set(a2.id, a2);
  }
  return Array.from(athleteMap.values());
}

export function getBracketDisplayName(categoryName?: string, groupId?: number): string {
  const name = categoryName ?? "";
  if (groupId && groupId !== 1) {
    return `${name} (Група ${groupId})`;
  }
  return name;
}
