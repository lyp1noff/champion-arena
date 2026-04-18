import { BACKEND_URL } from "@/lib/config";

import { Category } from "../interfaces";
import { fetchWithRefresh } from "./api";

export async function getCategories(): Promise<Category[]> {
  const res = await fetchWithRefresh(`${BACKEND_URL}/categories`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load categories");
  }

  return res.json();
}
