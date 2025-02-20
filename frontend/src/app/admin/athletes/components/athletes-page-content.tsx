"use client";

import { useEffect, useState } from "react";
import { getAthletes } from "@/lib/api/api";
import { DataTable } from "./data-table";
import { columns } from "./columns";
import { useTableState } from "./use-table-state";

export default function AthletesPageContent() {
  const { page, limit, sort, order } = useTableState();
  const [athletes, setAthletes] = useState([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    getAthletes(page, limit, sort, order).then(({ data, total }) => {
      setAthletes(data);
      setTotal(total);
    });
  }, [page, limit, sort, order]);

  return (
    <div className="container hidden h-full flex-1 flex-col space-y-8 p-8 md:flex">
      <DataTable data={athletes} columns={columns} total={total} />
    </div>
  );
}
