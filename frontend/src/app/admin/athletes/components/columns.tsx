import { ColumnDef } from "@tanstack/react-table";
import { Checkbox } from "@/components/ui/checkbox";
import DataTableColumnHeader from "@/components/data-table-column-header";
import { DataTableRowActions } from "@/components/data-table-row-actions";
import { Athlete } from "@/lib/interfaces";

export const columns: ColumnDef<Athlete>[] = [
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
    accessorKey: "last_name",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Last Name" />,
    cell: ({ row }) => <div>{row.getValue("last_name")}</div>,
    size: 200,
  },
  {
    accessorKey: "first_name",
    header: ({ column }) => <DataTableColumnHeader column={column} title="First Name" />,
    cell: ({ row }) => <div>{row.getValue("first_name")}</div>,
    size: 200,
  },
  {
    accessorKey: "gender",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Gender" />,
    cell: ({ row }) => <div>{row.getValue("gender")}</div>,
    size: 150,
  },
  {
    accessorKey: "age",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Age" />,
    cell: ({ row }) => <div>{row.getValue("age")}</div>,
    size: 20,
  },
  {
    accessorKey: "coach_last_name",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Coach" />,
    cell: ({ row }) => <div>{row.getValue("coach_last_name")}</div>,
    size: 150,
  },
  {
    id: "actions",
    cell: ({ row }) => <DataTableRowActions row={row} />,
    size: 20,
  },
];
