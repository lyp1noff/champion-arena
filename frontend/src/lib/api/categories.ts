import { Category } from "../interfaces";
import { fetchWithRefresh } from "./api";

const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getCategories(): Promise<Category[]> {
  const res = await fetchWithRefresh(`${url}/categories`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load categories");
  }

  return res.json();
}
