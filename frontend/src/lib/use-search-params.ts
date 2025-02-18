"use client";

import { useRouter, useSearchParams } from "next/navigation";

export function useUpdateParams() {
  const router = useRouter();
  const searchParams = useSearchParams();

  return (newParams: Record<string, string | number>) => {
    const params = new URLSearchParams(searchParams.toString());

    Object.entries(newParams).forEach(([key, value]) => {
      params.set(key, String(value));
    });

    if ("order_by" in newParams || "limit" in newParams) {
      params.set("page", "1");
    }

    router.replace(`?${params.toString()}`);
  };
}
