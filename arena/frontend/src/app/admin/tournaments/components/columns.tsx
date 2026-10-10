import { ColumnDef } from "@tanstack/react-table";

import { DateRange } from "@/components/date-range";
import DataTableColumnHeader from "@/components/table/data-table-column-header";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";

import { TOURNAMENT_STATUS, Tournament } from "@/lib/interfaces";

import { DataTableRowActions } from "./row-actions";

export function columns(onDataChanged: () => void, locale: string): ColumnDef<Tournament>[] {
  return [
    {
      id: "select",
      header: ({ table }) => (
        <Checkbox
          checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && "indeterminate")}
          onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
          aria-label="Select all"
          className="translate-y-[2px] ml-1"
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
          className="translate-y-[2px] ml-1"
        />
      ),
      size: 20,
      enableSorting: false,
      enableHiding: false,
    },
    {
      accessorKey: "name",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Name" />,
      cell: ({ row }) => <div>{row.getValue("name")}</div>,
      size: 200,
    },
    {
      id: "start_date",
      accessorKey: "start_date",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Date" />,
      cell: ({ row }) => <DateRange start={row.getValue("start_date")} end={row.original.end_date} locale={locale} />,
      size: 200,
    },
    {
      id: "status",
      accessorKey: "status",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
      cell: ({ row }) => {
        const status = row.getValue("status") as Tournament["status"];
        const getStatusVariant = (status: Tournament["status"]) => {
          switch (status) {
            case TOURNAMENT_STATUS.DRAFT:
              return "secondary";
            case TOURNAMENT_STATUS.UPCOMING:
              return "default";
            case TOURNAMENT_STATUS.STARTED:
              return "destructive";
            case TOURNAMENT_STATUS.FINISHED:
              return "outline";
            default:
              return "secondary";
          }
        };
        return <Badge variant={getStatusVariant(status)}>{status.charAt(0).toUpperCase() + status.slice(1)}</Badge>;
      },
      size: 200,
    },
    {
      id: "actions",
      cell: ({ row }) => <DataTableRowActions row={row} onDataChanged={onDataChanged} />,
      size: 20,
    },
  ];
}
