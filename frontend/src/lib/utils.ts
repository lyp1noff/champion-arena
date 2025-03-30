import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateToISO(date: Date): string {
  if (!date) throw new Error("Date is missing");
  return date.toISOString().split("T")[0]; // returns 'YYYY-MM-DD'
}
