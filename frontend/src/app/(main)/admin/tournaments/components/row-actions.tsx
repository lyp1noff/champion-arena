import {Row} from "@tanstack/react-table";
import {MoreHorizontal} from "lucide-react";

import {Button} from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {deleteTournament, downloadTournamentDocx} from "@/lib/api/tournaments";
import {toast} from "sonner";
import {Tournament} from "@/lib/interfaces";
import {sanitizeFilename} from "@/lib/utils";
import {useRouter} from "next/navigation";

interface DataTableRowActionsProps {
  row: Row<Tournament>;
  onDataChanged?: () => void;
}

export function DataTableRowActions({row, onDataChanged}: DataTableRowActionsProps) {
  const router = useRouter();

  const handleDelete = async () => {
    try {
      await deleteTournament(row.original.id);
      toast.success("Tournament deleted");
      onDataChanged?.();
    } catch (err) {
      toast.error(`Error deleting tournament: ${err}`);
    }
  };

  const handleOpen = () => {
    router.push(`/tournaments/${row.original.id}`);
  };

  const handleEdit = () => {
    router.push(`/admin/tournaments/edit/${row.original.id}`);
  };

  const handleManage = () => {
    router.push(`/admin/tournaments/manage/${row.original.id}`);
  };

  const exportFile = async () => {
    const filename = sanitizeFilename(row.original.name) || "tournament";

    toast.promise(
      (async () => {
        const blob = await downloadTournamentDocx(row.original.id);
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `${filename}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url);
      })(),
      {
        loading: "Generating file, please wait...",
        success: "File downloaded successfully",
        error: (err) => `Error exporting file: ${err}`,
      }
    );
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="flex h-8 w-8 p-0 data-[state=open]:bg-muted">
          <MoreHorizontal/>
          <span className="sr-only">Open menu</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-[160px]">
        <DropdownMenuItem onClick={handleOpen}>Open</DropdownMenuItem>
        <DropdownMenuItem onClick={handleEdit}>Edit</DropdownMenuItem>
        <DropdownMenuItem onClick={handleManage}>Manage</DropdownMenuItem>
        <DropdownMenuItem onClick={exportFile}>Export to File</DropdownMenuItem>
        <DropdownMenuSeparator/>
        <DropdownMenuItem onClick={handleDelete}>Delete</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
