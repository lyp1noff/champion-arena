import { useState } from "react";
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
import { deleteTournament, downloadTournamentDocx } from "@/lib/api/tournaments";
import { toast } from "sonner";
import { Tournament } from "@/lib/interfaces";
import { useRouter } from "next/navigation";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { TournamentForm } from "@/components/tournament-form";
import { useTranslations } from "next-intl";

interface DataTableRowActionsProps {
  row: Row<Tournament>;
  onDataChanged?: () => void;
}

export function DataTableRowActions({ row, onDataChanged }: DataTableRowActionsProps) {
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const router = useRouter();
  const t = useTranslations("AdminTournaments");

  const handleDelete = async () => {
    try {
      await deleteTournament(row.original.id);
      toast.success("Tournament deleted");
      onDataChanged?.();
    } catch (err) {
      toast.error(`Error deleting tournament: ${err}`);
    }
    setIsDeleteDialogOpen(false);
  };

  const handleOpen = () => {
    router.push(`/tournaments/${row.original.id}`);
  };

  const handleEdit = () => setIsEditDialogOpen(true);

  const handleManage = () => {
    router.push(`/admin/tournaments/${row.original.id}/manage`);
  };

  const handleApplications = () => {
    router.push(`/admin/tournaments/${row.original.id}/applications`);
  };

  const exportFile = async () => {
    toast.promise(
      (async () => {
        const url = await downloadTournamentDocx(row.original.id);
        window.open(url, "_blank");
      })(),
      {
        loading: "Generating file, please wait...",
        success: "File exported successfully",
        error: (err) => `Error exporting file: ${err}`,
      },
    );
  };

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="flex h-8 w-8 p-0 data-[state=open]:bg-muted">
            <MoreHorizontal />
            <span className="sr-only">Open menu</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-[160px]">
          <DropdownMenuItem onClick={handleOpen}>{t("open")}</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleEdit}>{t("edit")}</DropdownMenuItem>
          <DropdownMenuItem onClick={handleApplications}>{t("applications")}</DropdownMenuItem>
          <DropdownMenuItem onClick={handleManage}>{t("manage")}</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={exportFile}>{t("exportToFile")}</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setIsDeleteDialogOpen(true)}>{t("delete")}</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogTitle>Edit Tournament</DialogTitle>
          <TournamentForm
            tournamentId={row.original.id}
            onSuccess={() => {
              setIsEditDialogOpen(false);
              onDataChanged?.();
            }}
          />
        </DialogContent>
      </Dialog>

      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogTitle>{t("deleteConfirmTitle")}</DialogTitle>
          <p>{t("deleteConfirmText")}</p>
          <div className="flex justify-end gap-2 mt-4">
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              {t("deleteConfirmCancel")}
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              {t("deleteConfirmDelete")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
