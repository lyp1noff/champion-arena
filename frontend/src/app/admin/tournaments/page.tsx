"use client";

import { Suspense } from "react";
import DataTable from "@/components/data-table";
import ScreenLoader from "@/components/loader";
import useDataTable from "./hooks/use-data-table";
import { columns } from "./components/columns";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import Link from "next/link";

function TournamentTableWrapper() {
  const {
    data,
    totalPages,
    totalRecords,
    pagination,
    onPaginationChange,
    sorting,
    onSortingChange,
    search,
    setSearch,
  } = useDataTable();

  return (
    <div className="container h-full flex-1 flex-col p-8 md:flex">
      <div className="flex gap-4 mb-4">
        <Input
          placeholder="Search tournament..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value.trim())}
        />
        <Link href="/admin/tournaments/create">
          <Button variant="outline">Create New Tournament</Button>
        </Link>
      </div>
      <DataTable
        columns={columns}
        data={data}
        totalPages={totalPages}
        totalRecords={totalRecords}
        pagination={pagination}
        setPagination={onPaginationChange}
        sorting={sorting}
        setSorting={onSortingChange}
      />
    </div>
  );
}

export default function TournamentsPage() {
  return (
    <Suspense fallback={<ScreenLoader />}>
      <TournamentTableWrapper />
    </Suspense>
  );
}
