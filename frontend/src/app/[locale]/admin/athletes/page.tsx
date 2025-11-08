"use client";

import { Suspense } from "react";

import { Link } from "@/i18n/navigation";

import ScreenLoader from "@/components/loader";
import DataTable from "@/components/table/data-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import useDataTable from "./hooks/use-data-table";

function AthletesTableWrapper() {
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
    coachSearch,
    setCoachSearch,
    columns,
  } = useDataTable();

  return (
    <div className="container h-full flex-1 flex-col p-8 md:flex">
      <div className="flex gap-4 mb-4">
        <Input placeholder="Search athlete..." value={search} onChange={(e) => setSearch(e.target.value.trim())} />
        <Input
          placeholder="Search coach..."
          value={coachSearch}
          onChange={(e) => setCoachSearch(e.target.value.trim())}
        />

        <Link href="/admin/athletes/create">
          <Button variant="outline">Create New Athlete</Button>
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

export default function AthletesPage() {
  return (
    <Suspense fallback={<ScreenLoader />}>
      <AthletesTableWrapper />
    </Suspense>
  );
}
