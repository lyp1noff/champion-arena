import { useState, useEffect } from "react";
import { PaginationState, SortingState, Updater } from "@tanstack/react-table";
import { getAthletes } from "@/lib/api/api";
import { useSearchParams, useRouter } from "next/navigation";
import { Athlete } from "@/lib/interfaces";

export default function useDataTable() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const pageFromUrl = Number(searchParams.get("page")) || 1;
  const pageSizeFromUrl = Number(searchParams.get("size")) || 10;
  const sortFromUrl = searchParams.get("sort") || "last_name";
  const orderFromUrl = searchParams.get("order") === "desc" ? "desc" : "asc";

  const [data, setData] = useState<Athlete[]>([]);
  const [totalPages, setTotalPages] = useState(0);
  const [totalRecords, setTotalRecords] = useState(0);

  const [pagination, setPagination] = useState<PaginationState>({
    pageIndex: pageFromUrl - 1,
    pageSize: pageSizeFromUrl,
  });

  const [sorting, setSorting] = useState<SortingState>([
    { id: sortFromUrl, desc: orderFromUrl === "desc" },
  ]);

  const onPaginationChange: typeof setPagination = (updater) => {
    setPagination((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      return next.pageSize !== prev.pageSize ? { ...next, pageIndex: 0 } : next;
    });
  };

  const onSortingChange: typeof setSorting = (updater) => {
    setSorting((prev) => {
      const next = typeof updater === "function" ? updater(prev) : updater;
      setPagination((p) => ({ ...p, pageIndex: 0 }));
      return next;
    });
  };

  useEffect(() => {
    const params = new URLSearchParams();
    params.set("page", String(pagination.pageIndex + 1));
    params.set("size", String(pagination.pageSize));
    params.set("sort", sorting[0]?.id || "last_name");
    params.set("order", sorting[0]?.desc ? "desc" : "asc");

    router.replace(`?${params.toString()}`);
  }, [pagination, sorting, router]);

  useEffect(() => {
    const sortField = sorting.length > 0 ? sorting[0].id : "last_name";
    const sortOrder = sorting.length > 0 && sorting[0].desc ? "desc" : "asc";

    getAthletes(pagination.pageIndex + 1,
      pagination.pageSize,
      sortField,
      sortOrder).then(({ data, total, limit }) => {
        setData(data);
        setTotalRecords(total);
        setTotalPages(Math.ceil(total / limit));
    });
  }, [pagination, sorting]);

  return { data, totalPages, totalRecords, pagination, onPaginationChange, sorting, onSortingChange };
}
