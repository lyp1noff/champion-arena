"use client";

import { useRouter, useSearchParams } from "next/navigation";

export function useTableState() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const page = parseInt(searchParams.get("page") || "1", 10);
  const limit = parseInt(searchParams.get("limit") || "10", 10);
  const sort = searchParams.get("sort") || "";
  const order = searchParams.get("order") || "asc";

  const updateParams = (newParams: Record<string, string | number | null>) => {
    const params = new URLSearchParams(searchParams.toString());

    Object.entries(newParams).forEach(([key, value]) => {
      if (value === null) {
        params.delete(key);
      } else {
        params.set(key, String(value));
      }
    });

    if ("sort" in newParams || "limit" in newParams) {
      params.set("page", "1");
    }

    router.replace(`?${params.toString()}`);
  };

  return {
    page,
    limit,
    sort,
    order,
    updateParams,
  };
}
