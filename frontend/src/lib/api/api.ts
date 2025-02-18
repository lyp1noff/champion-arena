const url = "http://localhost:8000"

export async function getAthletes(
    page: number = 1,
    limit: number = 10,
    orderBy: string = "last_name",
    order: string = "asc"
  ) {
    const res = await fetch(
      `${url}/athletes?page=${page}&limit=${limit}&order_by=${orderBy}&order=${order}`,
      { cache: "no-store" }
    );
  
    if (!res.ok) {
      throw new Error("Ошибка загрузки данных");
    }
  
    return res.json();
  }
  