"use client";

import { Suspense } from "react";

import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";

import ScreenLoader from "@/components/loader";
import DataTable from "@/components/table/data-table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import useDataTable from "./hooks/use-data-table";

function TournamentTableWrapper() {
  const t = useTranslations("AdminTournaments");

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
    columns,
  } = useDataTable();

  return (
    <div className="container h-full flex-1 flex-col p-8 md:flex">
      <div className="flex gap-4 mb-4">
        <Input
          placeholder={t("search")}
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearch(e.target.value.trim())}
        />
        <Link href="/admin/tournaments/create">
          <Button variant="outline">{t("create")}</Button>
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
