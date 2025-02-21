"use client";

import { Suspense } from "react";
import DataTable from "../../../components/data-table";
import ScreenLoader from "@/components/loader";
import { columns } from "./components/columns";
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
  } = useDataTable();

  return (
    <DataTable
      columns={columns}
      data={data}
      totalPages={totalPages}
      totalRecords={totalRecords}
      pagination={pagination}
      setPagination={onPaginationChange}
      sorting={sorting}
      setSorting={onSortingChange}
      search={search}
      setSearch={setSearch}
      coachSearch={coachSearch}
      setCoachSearch={setCoachSearch}
    />
  );
}

export default function AthletesPage() {
  return (
    <div className="container h-full flex-1 flex-col space-y-8 p-8 md:flex">
      <Suspense fallback={<ScreenLoader />}>
        <AthletesTableWrapper />
      </Suspense>
    </div>
  );
}
