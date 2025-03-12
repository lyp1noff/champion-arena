const url = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000/api";

export async function getAthletes(
  page: number = 1,
  limit: number = 10,
  orderBy: string = "last_name",
  order: string = "asc",
  search: string = "",
  coach_search: string = ""
) {
  const res = await fetch(
    `${url}/athletes?page=${page}&limit=${limit}&order_by=${orderBy}&order=${order}&search=${search}&coach_search=${coach_search}`,
    { cache: "no-store" }
  );

  if (!res.ok) {
    throw new Error("Ошибка загрузки данных");
  }

  return res.json();
}

export async function getCoaches() {
  const res = await fetch(`${url}/coaches`, { cache: "no-store" });

  if (!res.ok) {
    throw new Error("Ошибка загрузки данных");
  }

  return res.json();
}

export async function uploadPhoto(file: File, path: string): Promise<string | null> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("path", path);

  try {
    const response = await fetch(`${url}/upload/photo`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Failed to upload");

    const data = await response.json();
    return `${process.env.NEXT_PUBLIC_CDN_URL}/${data.url}`;
  } catch (error) {
    console.error("Error while uploading file", error);
    return null;
  }
}
