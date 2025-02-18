"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { columns } from "./components/columns";
import { DataTable } from "./components/data-table";
import { getAthletes } from "@/lib/api/api";
import FullScreenLoader from "@/components/loader";

export default function AthletesPage() {
  return (
    <Suspense fallback={<FullScreenLoader />}>
      <AthletesPageContent />
    </Suspense>
  );
}

function AthletesPageContent() {
  const searchParams = useSearchParams();

  const page = Number(searchParams.get("page") || "1");
  const limit = Number(searchParams.get("limit") || "10");
  const orderBy = searchParams.get("order_by") || "last_name";
  const order = searchParams.get("order") || "asc";

  const [athletes, setAthletes] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getAthletes(page, limit, orderBy, order)
      .then(({ data, total }) => {
        setAthletes(data);
        setTotal(total);
      })
      .finally(() => setLoading(false));
  }, [page, limit, orderBy, order]);

  // if (loading) return <p>Loading athletes...</p>;

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
