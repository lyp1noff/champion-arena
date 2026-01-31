import { useState } from "react";

import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";

import { Row } from "@tanstack/react-table";
import { MoreHorizontal } from "lucide-react";
import { toast } from "sonner";

import { TournamentForm } from "@/components/tournament-form";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import {
  deleteTournament,
  downloadTournamentDocx,
  startTournament,
  updateTournamentStatus,
} from "@/lib/api/tournaments";
import { Tournament } from "@/lib/interfaces";

interface DataTableRowActionsProps {
  row: Row<Tournament>;
  onDataChanged?: () => void;
}

export function DataTableRowActions({ row, onDataChanged }: DataTableRowActionsProps) {
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const router = useRouter();
  const t = useTranslations("AdminTournaments");
  const tournament = row.original;

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

  const handleReports = () => {
    router.push(`/admin/tournaments/${row.original.id}/reports`);
  };

  const handleStartTournament = async () => {
    if (!tournament) return;
    try {
      await startTournament(tournament.id);
      toast.success("Tournament started successfully");
      onDataChanged?.();
    } catch {
      toast.error("Failed to start tournament");
    }
  };

  const handleUpdateStatus = async (newStatus: string) => {
    if (!tournament) return;
    try {
      await updateTournamentStatus(tournament.id, newStatus);
      toast.success(`Tournament status updated to ${newStatus}`);
      onDataChanged?.();
    } catch {
      toast.error("Failed to update tournament status");
    }
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
          <DropdownMenuItem onClick={handleReports}>{t("reports")}</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>Update Status</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuItem onClick={() => handleUpdateStatus("draft")}>Set to Draft</DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleUpdateStatus("upcoming")}>Set to Upcoming</DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleUpdateStatus("started")}>Set to Started</DropdownMenuItem>
              <DropdownMenuItem onClick={() => handleUpdateStatus("finished")}>Set to Finished</DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
          {tournament.status === "upcoming" && (
            <DropdownMenuItem onClick={handleStartTournament}>Start Tournament</DropdownMenuItem>
          )}
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
