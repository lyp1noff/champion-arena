import {
  Bracket,
  BracketCreate,
  BracketDelete,
  BracketMatchesResponse,
  BracketUpdate,
  CategoryCreate,
  ParticipantMove,
  ParticipantReorder,
} from "../interfaces";
import { fetchWithRefresh } from "./api";

const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getBracketsById(id: number): Promise<Bracket> {
  const res = await fetchWithRefresh(`${url}/brackets/${id}`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load bracket");
  }

  return res.json();
}

export async function getBracketMatchesById(id: number): Promise<BracketMatchesResponse> {
  const res = await fetchWithRefresh(`${url}/brackets/${id}/matches`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load bracket");
  }

  return res.json();
}

export async function updateBracket(bracketId: number, updateData: BracketUpdate) {
  const response = await fetchWithRefresh(`${url}/brackets/${bracketId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updateData),
  });

  if (!response.ok) {
    throw new Error("Failed to update bracket");
  }

  return await response.json();
}

export async function regenerateBracket(bracketId: number) {
  const response = await fetchWithRefresh(`${url}/brackets/${bracketId}/regenerate`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to regenerate bracket");
  }

  return await response.json();
}

export async function moveParticipant(moveData: ParticipantMove) {
  const response = await fetchWithRefresh(`${url}/brackets/participants/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(moveData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to move participant");
  }

  return await response.json();
}

export async function reorderParticipants(participantsData: ParticipantReorder) {
  const response = await fetchWithRefresh(`${url}/brackets/participants/reorder`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(participantsData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to reorder participants");
  }

  return await response.json();
}

export async function createBracket(bracketData: BracketCreate) {
  const response = await fetchWithRefresh(`${url}/brackets/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bracketData),
  });

  if (!response.ok) {
    throw new Error("Failed to create bracket");
  }

  return await response.json();
}

export async function deleteBracket(bracketId: number, bracketData: BracketDelete) {
  const response = await fetchWithRefresh(`${url}/brackets/${bracketId}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(bracketData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Failed to delete bracket");
  }

  return await response.json();
}

export async function getCategories() {
  const response = await fetchWithRefresh(`${url}/categories`);

  if (!response.ok) {
    throw new Error("Failed to fetch categories");
  }

  return await response.json();
}

export async function createCategory(categoryData: CategoryCreate) {
  const response = await fetchWithRefresh(`${url}/categories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(categoryData),
  });

  if (!response.ok) {
    throw new Error("Failed to create category");
  }

  return await response.json();
}

export async function updateBracketStatus(bracketId: number, status: string) {
  const response = await fetchWithRefresh(`${url}/brackets/${bracketId}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });

  if (!response.ok) {
    throw new Error("Failed to update bracket status");
  }

  return await response.json();
}

export async function startBracket(bracketId: number) {
  const response = await fetchWithRefresh(`${url}/brackets/${bracketId}/start`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error("Failed to start bracket");
  }

  return await response.json();
}
