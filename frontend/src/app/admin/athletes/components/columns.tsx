"use client";

import { ColumnDef } from "@tanstack/react-table";

import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";

import { labels, priorities, statuses } from "../data/data";
import { Athlete } from "../data/schema";
import { DataTableColumnHeader } from "./data-table-column-header";
import { DataTableRowActions } from "./data-table-row-actions";

function calculateAge(birthDate: string): number {
  const today = new Date();
  const birth = new Date(birthDate);
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }

  return age;
}

export const columns: ColumnDef<Athlete>[] = [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && "indeterminate")}
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
        className="translate-y-[2px]"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
        className="translate-y-[2px]"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  // {
  //   accessorKey: "status",
  //   header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
  //   cell: ({ row }) => <div>{row.getValue("first_name")}</div>,
  //   filterFn: (row, id, value) => {
  //     return value.includes(row.getValue(id));
  //   },
  // },
  {
    accessorKey: "last_name",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Last Name" />,
    cell: ({ row }) => <div>{row.getValue("last_name")}</div>,
  },
  {
    accessorKey: "first_name",
    header: ({ column }) => <DataTableColumnHeader column={column} title="First Name" />,
    cell: ({ row }) => <div>{row.getValue("first_name")}</div>,
  },
  {
    accessorKey: "gender",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Gender" />,
    cell: ({ row }) => <div>{row.getValue("gender")}</div>,
  },
  {
    accessorKey: "birth_date",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Age" />,
    cell: ({ row }) => <div>{calculateAge(row.getValue("birth_date"))}</div>,
  },
  {
    accessorKey: "coach_id",
    header: ({ column }) => <DataTableColumnHeader column={column} title="Coach" />,
    cell: ({ row }) => <div>{row.getValue("coach_id")}</div>,
  },
  {
    id: "actions",
    cell: ({ row }) => <DataTableRowActions row={row} />,
  },
];

// export const columns: ColumnDef<Athlete>[] = [
//   {
//     id: "select",
//     header: ({ table }) => (
//       <Checkbox
//         checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && "indeterminate")}
//         onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
//         aria-label="Select all"
//         className="translate-y-[2px]"
//       />
//     ),
//     cell: ({ row }) => (
//       <Checkbox
//         checked={row.getIsSelected()}
//         onCheckedChange={(value) => row.toggleSelected(!!value)}
//         aria-label="Select row"
//         className="translate-y-[2px]"
//       />
//     ),
//     enableSorting: false,
//     enableHiding: false,
//   },
//   {
//     accessorKey: "id",
//     header: ({ column }) => <DataTableColumnHeader column={column} title="Task" />,
//     cell: ({ row }) => <div className="w-[80px]">{row.getValue("id")}</div>,
//     enableSorting: false,
//     enableHiding: false,
//   },
//   {
//     accessorKey: "title",
//     header: ({ column }) => <DataTableColumnHeader column={column} title="Title" />,
//     cell: ({ row }) => {
//       const label = labels.find((label) => label.value === row.original.label);

//       return (
//         <div className="flex space-x-2">
//           {label && <Badge variant="outline">{label.label}</Badge>}
//           <span className="max-w-[500px] truncate font-medium">{row.getValue("title")}</span>
//         </div>
//       );
//     },
//   },
//   {
//     accessorKey: "status",
//     header: ({ column }) => <DataTableColumnHeader column={column} title="Status" />,
//     cell: ({ row }) => {
//       const status = statuses.find((status) => status.value === row.getValue("status"));

//       if (!status) {
//         return null;
//       }

//       return (
//         <div className="flex w-[100px] items-center">
//           {status.icon && <status.icon className="mr-2 h-4 w-4 text-muted-foreground" />}
//           <span>{status.label}</span>
//         </div>
//       );
//     },
//     filterFn: (row, id, value) => {
//       return value.includes(row.getValue(id));
//     },
//   },
//   {
//     accessorKey: "priority",
//     header: ({ column }) => <DataTableColumnHeader column={column} title="Priority" />,
//     cell: ({ row }) => {
//       const priority = priorities.find((priority) => priority.value === row.getValue("priority"));

//       if (!priority) {
//         return null;
//       }

//       return (
//         <div className="flex items-center">
//           {priority.icon && <priority.icon className="mr-2 h-4 w-4 text-muted-foreground" />}
//           <span>{priority.label}</span>
//         </div>
//       );
//     },
//     filterFn: (row, id, value) => {
//       return value.includes(row.getValue(id));
//     },
//   },
//   {
//     id: "actions",
//     cell: ({ row }) => <DataTableRowActions row={row} />,
//   },
// ];
