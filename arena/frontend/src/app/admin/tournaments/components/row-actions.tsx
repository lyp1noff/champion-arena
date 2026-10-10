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
  downloadTournamentPdf,
  startTournament,
  updateTournamentStatus,
} from "@/lib/api/tournaments";
import type { TournamentExportMode } from "@/lib/api/tournaments";
import { TOURNAMENT_STATUS, Tournament } from "@/lib/interfaces";

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
    router.push(`/admin/tournaments/${row.original.id}`);
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

  const exportFile = async (mode: TournamentExportMode) => {
    toast.promise(
      (async () => {
        const url = await downloadTournamentPdf(row.original.id, mode);
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
          {tournament.status === TOURNAMENT_STATUS.DRAFT && (
            <DropdownMenuItem onClick={() => handleUpdateStatus(TOURNAMENT_STATUS.UPCOMING)}>Publish Tournament</DropdownMenuItem>
          )}
          {tournament.status === TOURNAMENT_STATUS.UPCOMING && (
            <DropdownMenuItem onClick={handleStartTournament}>Start Tournament</DropdownMenuItem>
          )}
          {tournament.status === TOURNAMENT_STATUS.STARTED && (
            <DropdownMenuItem onClick={() => handleUpdateStatus(TOURNAMENT_STATUS.FINISHED)}>Finish Tournament</DropdownMenuItem>
          )}
          <DropdownMenuSeparator />
          <DropdownMenuSub>
            <DropdownMenuSubTrigger>{t("exportToFile")}</DropdownMenuSubTrigger>
            <DropdownMenuSubContent>
              <DropdownMenuItem onClick={() => exportFile("filled")}>{t("exportFilled")}</DropdownMenuItem>
              <DropdownMenuItem onClick={() => exportFile("manual")}>{t("exportManual")}</DropdownMenuItem>
            </DropdownMenuSubContent>
          </DropdownMenuSub>
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
