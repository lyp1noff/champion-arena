import { BACKEND_URL } from "@/lib/config";
import { Coach, CoachInput } from "@/lib/interfaces";
import { isClient } from "@/lib/utils";

export async function fetchWithRefresh(input: RequestInfo, init?: RequestInit): Promise<Response> {
  let response = await fetch(input, { ...init, credentials: "include" });

  if (isClient && response.status === 401) {
    try {
      const refreshRes = await fetch(`${BACKEND_URL}/auth/refresh`, {
        method: "POST",
        credentials: "include",
      });

      if (refreshRes.ok) {
        response = await fetch(input, {
          ...init,
          credentials: "include",
        });
      } else {
        window.location.href = "/login";
      }
    } catch (err) {
      console.error("refresh failed", err);
      window.location.href = "/login";
    }
  }

  return response;
}

async function apiError(response: Response, fallback: string): Promise<Error> {
  const data = await response.json().catch(() => null);
  return new Error(typeof data?.detail === "string" ? data.detail : fallback);
}

export async function getCoaches(): Promise<Coach[]> {
  const res = await fetchWithRefresh(`${BACKEND_URL}/coaches`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load coaches");
  }

  return res.json();
}

export async function createCoach(data: CoachInput): Promise<Coach> {
  const res = await fetchWithRefresh(`${BACKEND_URL}/coaches`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await apiError(res, "Failed to create coach");
  return res.json();
}

export async function updateCoach(id: number, data: CoachInput): Promise<Coach> {
  const res = await fetchWithRefresh(`${BACKEND_URL}/coaches/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await apiError(res, "Failed to update coach");
  return res.json();
}

export async function deleteCoach(id: number): Promise<void> {
  const res = await fetchWithRefresh(`${BACKEND_URL}/coaches/${id}`, { method: "DELETE" });
  if (!res.ok) throw await apiError(res, "Failed to delete coach");
}

export async function uploadImage(file: File, path: string): Promise<string | null> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("path", path);

  try {
    const response = await fetchWithRefresh(`${BACKEND_URL}/upload/photo`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Failed to upload");

    const data = await response.json();
    return data.url;
  } catch (error) {
    console.error("Error while uploading file", error);
    return null;
  }
}
