import { BACKEND_URL } from "@/lib/config";
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

export async function getCoaches() {
  const res = await fetchWithRefresh(`${BACKEND_URL}/coaches`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Failed to load coaches");
  }

  return res.json();
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
