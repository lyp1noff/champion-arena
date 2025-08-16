import { Row } from "@tanstack/react-table";
import { MoreHorizontal } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Athlete } from "@/lib/interfaces";
import { toast } from "sonner";
import { deleteAthlete } from "@/lib/api/athletes";

interface DataTableRowActionsProps {
  row: Row<Athlete>;
  onDataChanged?: () => void;
}

export function DataTableRowActions({ row, onDataChanged }: DataTableRowActionsProps) {
  const handleDelete = async () => {
    try {
      await deleteAthlete(row.original.id);
      toast.success("Athlete deleted");
      onDataChanged?.();
    } catch (err) {
      toast.error(`Error deleting athlete: ${err}`);
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="flex h-8 w-8 p-0 data-[state=open]:bg-muted">
          <MoreHorizontal />
          <span className="sr-only">Open menu</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[160px]">
        <DropdownMenuItem
          onClick={() => {
            console.log(row);
          }}
        >
          Edit
        </DropdownMenuItem>
        {/*<DropdownMenuItem*/}
        {/*  onClick={() => {*/}
        {/*    console.log(row);*/}
        {/*  }}*/}
        {/*>*/}
        {/*  Make a copy*/}
        {/*</DropdownMenuItem>*/}
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleDelete}>Delete</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
