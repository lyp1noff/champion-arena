import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table } from "@tanstack/react-table";
import { useTranslations } from "next-intl";

interface DataTablePaginationProps<TData> {
  table: Table<TData>;
  totalRecords: number;
  pageSizeOptions?: number[];
}

export default function DataTablePagination<TData>({
  table,
  totalRecords,
  pageSizeOptions = [10, 20, 30, 40, 50],
}: DataTablePaginationProps<TData>) {
  const t = useTranslations("DataTable");

  return (
    <div className="flex flex-col items-center gap-2 mt-4 w-full lg:flex-row lg:justify-between">
      <div className="text-sm text-muted-foreground text-center lg:ml-2">
        {table.getFilteredSelectedRowModel().rows.length} {t("of")} {table.getFilteredRowModel().rows.length}{" "}
        {t("rowsSelected")} | {t("totalRecords")}: {totalRecords}
      </div>
      <div className="flex flex-col items-center gap-2 lg:flex-row lg:gap-6">
        <div className="flex items-center space-x-2">
          <p className="text-sm font-medium">{t("rowsPerPage")}</p>
          <Select
            value={`${table.getState().pagination.pageSize}`}
            onValueChange={(value) => table.setPageSize(Number(value))}
          >
            <SelectTrigger className="h-8 w-[70px]">
              <SelectValue placeholder={table.getState().pagination.pageSize} />
            </SelectTrigger>
            <SelectContent side="top">
              {pageSizeOptions.map((pageSize) => (
                <SelectItem key={pageSize} value={`${pageSize}`}>
                  {pageSize}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="text-sm font-medium">
          {t("page")} {table.getState().pagination.pageIndex + 1} {t("of")} {table.getPageCount()}
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            className="h-8 w-8 p-0 lg:flex"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">{t("firstPage")}</span>
            <ChevronsLeft />
          </Button>
          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <span className="sr-only">{t("prevPage")}</span>
            <ChevronLeft />
          </Button>
          <Button
            variant="outline"
            className="h-8 w-8 p-0"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <span className="sr-only">{t("nextPage")}</span>
            <ChevronRight />
          </Button>
          <Button
            variant="outline"
            className="h-8 w-8 p-0 lg:flex"
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
          >
            <span className="sr-only">{t("lastPage")}</span>
            <ChevronsRight />
          </Button>
        </div>
      </div>
    </div>
  );
}
