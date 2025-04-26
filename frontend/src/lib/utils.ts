import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

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

  const timeRegex = /^([01]\d|2[0-3]):([0-5]\d)$/;
  if (!timeRegex.test(timeStr)) {
    console.warn(`Invalid time format: ${timeStr}`);
    return null;
  }

  return `${timeStr}:00`;
}

export function getInitialMatchCount(participantCount: number): number {
  const half = participantCount / 2;
  return 2 ** Math.ceil(Math.log2(half));
}

export function getBracketDimensions(matchCardHeight: number, matchCardWidth?: number) {
  const cardHeight = matchCardHeight;
  const cardWidth = matchCardWidth ?? cardHeight * 3;
  const roundTitleHeight = cardHeight / 3;
  const columnGap = (cardHeight / 8) * 2;

  return { cardHeight, cardWidth, roundTitleHeight, columnGap };
}
