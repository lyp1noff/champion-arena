"use client";

import { Suspense } from "react";
import DataTable from "@/components/data-table";
import ScreenLoader from "@/components/loader";
import useDataTable from "./hooks/use-data-table";
import { columns } from "./components/columns";
import DataTableSearch from "./components/data-table-search";

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
  } = useDataTable();

  return (
    <div className="container h-full flex-1 flex-col p-8 md:flex">
      <DataTableSearch
        search={search}
        setSearch={setSearch}
        coachSearch={coachSearch}
        setCoachSearch={setCoachSearch}
      />
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
