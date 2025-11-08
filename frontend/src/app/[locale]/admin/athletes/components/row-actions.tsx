import { useState } from "react";

import { useTranslations } from "next-intl";

import { Row } from "@tanstack/react-table";
import { MoreHorizontal } from "lucide-react";
import { toast } from "sonner";

import AthleteForm from "@/components/athlete-form";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { deleteAthlete } from "@/lib/api/athletes";
import { Athlete } from "@/lib/interfaces";

interface DataTableRowActionsProps {
  row: Row<Athlete>;
  onDataChanged?: () => void;
}

export function DataTableRowActions({ row, onDataChanged }: DataTableRowActionsProps) {
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);

  const t = useTranslations("AdminAthletes");

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
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="flex h-8 w-8 p-0 data-[state=open]:bg-muted">
            <MoreHorizontal />
            <span className="sr-only">Open menu</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-[160px]">
          <DropdownMenuItem onClick={() => setIsEditDialogOpen(true)}>{t("edit")}</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setIsDeleteDialogOpen(true)}>{t("delete")}</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogTitle>Edit Athlete</DialogTitle>
          <AthleteForm
            athleteId={row.original.id}
            onSuccess={() => {
              toast.success("Athlete updated");
              setIsEditDialogOpen(false);
              onDataChanged?.();
            }}
            onCancel={() => setIsEditDialogOpen(false)}
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
