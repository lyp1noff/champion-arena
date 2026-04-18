import { Column } from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";

import { Button } from "@/components/ui/button";

interface DataTableHeaderProps<TData> {
  column: Column<TData, unknown>;
  title: string;
}

export default function DataTableColumnHeader<TData>({ column, title }: DataTableHeaderProps<TData>) {
  return (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-3 h-8"
      onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
    >
      <span>{title}</span>
      {column.getIsSorted() === "asc" ? (
        <ArrowDown />
      ) : column.getIsSorted() === "desc" ? (
        <ArrowUp />
      ) : (
        <ChevronsUpDown />
      )}
    </Button>
  );
}
