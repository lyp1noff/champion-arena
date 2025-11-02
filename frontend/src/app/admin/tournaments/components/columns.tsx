import { ColumnDef } from "@tanstack/react-table";

import DataTableColumnHeader from "@/components/table/data-table-column-header";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";

import { Tournament } from "@/lib/interfaces";

import { DataTableRowActions } from "./row-actions";

export function columns(onDataChanged: () => void): ColumnDef<Tournament>[] {
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
      accessorKey: "location",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Location" />,
      cell: ({ row }) => <div>{row.getValue("location")}</div>,
      size: 200,
    },
    {
      accessorKey: "start_date",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Date" />,
      cell: ({ row }) => <div>{row.getValue("start_date")}</div>,
      size: 200,
    },
    {
      accessorKey: "status",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
      cell: ({ row }) => {
        const status = row.getValue("status") as string;
        const getStatusVariant = (status: string) => {
          switch (status) {
            case "draft":
              return "secondary";
            case "upcoming":
              return "default";
            case "started":
              return "destructive";
            case "finished":
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
      accessorKey: "participants",
      header: ({ column }) => <DataTableColumnHeader column={column} title="Participants" />,
      cell: ({ row }) => <div>{row.getValue("participants")}</div>,
      size: 50,
    },
    {
      id: "actions",
      cell: ({ row }) => <DataTableRowActions row={row} onDataChanged={onDataChanged} />,
      size: 20,
    },
  ];
}
