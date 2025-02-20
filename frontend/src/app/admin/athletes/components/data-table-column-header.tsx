import { ArrowDown, ArrowUp, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useTableState } from "./use-table-state";

interface DataTableColumnHeaderProps {
  title: string;
  sortingField: string;
}

export function DataTableColumnHeader({ title, sortingField }: DataTableColumnHeaderProps) {
  const { sort, order, updateParams } = useTableState();

  const isSorted = sort === sortingField;
  const nextOrder = isSorted && order === "asc" ? "desc" : "asc";

  return (
    <Button
      variant="ghost"
      size="sm"
      className="-ml-3 h-8"
      onClick={() => updateParams({ sort: sortingField, order: nextOrder })}
    >
      <span>{title}</span>
      {isSorted ? order === "desc" ? <ArrowDown /> : <ArrowUp /> : <ChevronsUpDown />}
    </Button>
  );
}
