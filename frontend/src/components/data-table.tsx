import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useReactTable, getCoreRowModel, flexRender, ColumnDef } from "@tanstack/react-table";
import DataTablePagination from "@/components/data-table-pagination";

interface DataTableProps<TData> {
  columns: ColumnDef<TData>[];
  data: TData[];
  totalPages: number;
  totalRecords: number;
  pagination: any;
  setPagination: any;
  sorting: any;
  setSorting: any;
}

export default function DataTable<TData>({
  columns,
  data,
  totalPages,
  totalRecords,
  pagination,
  setPagination,
  sorting,
  setSorting,
}: DataTableProps<TData>) {
  const table = useReactTable({
    data,
    columns,
    pageCount: totalPages,
    state: { pagination, sorting },
    onPaginationChange: setPagination,
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
  });

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id} colSpan={header.colSpan} style={{ width: header.getSize() }}>
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="p-1 pl-2">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  Нет данных.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      <DataTablePagination table={table} totalRecords={totalRecords} />
    </div>
  );
}
