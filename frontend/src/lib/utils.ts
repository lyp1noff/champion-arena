import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateToISO(date: Date): string {
  if (!date) throw new Error("Date is missing");
  return date.toISOString().split("T")[0]; // returns 'YYYY-MM-DD'
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
