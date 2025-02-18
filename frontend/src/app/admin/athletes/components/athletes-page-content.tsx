"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getAthletes } from "@/lib/api/api";
import { DataTable } from "./data-table";
import { columns } from "./columns";

export default function AthletesPageContent() {
  const searchParams = useSearchParams();

  const page = Number(searchParams.get("page") || "1");
  const limit = Number(searchParams.get("limit") || "10");
  const orderBy = searchParams.get("order_by") || "last_name";
  const order = searchParams.get("order") || "asc";

  const [athletes, setAthletes] = useState([]);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    getAthletes(page, limit, orderBy, order).then(({ data, total }) => {
      setAthletes(data);
      setTotal(total);
    });
  }, [page, limit, orderBy, order]);

  return (
    <div className="container hidden h-full flex-1 flex-col space-y-8 p-8 md:flex">
      <DataTable
        data={athletes}
        columns={columns}
        total={total}
        limit={limit}
        page={page}
        orderBy={orderBy}
        order={order}
      />
    </div>
  );
}
