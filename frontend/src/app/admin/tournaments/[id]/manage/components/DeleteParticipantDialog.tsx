import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Participant } from "@/lib/interfaces";
import React from "react";

interface DeleteParticipantDialogProps {
  open: boolean;
  onClose: () => void;
  participantToDelete: Participant | null;
  isLoading?: boolean;
  onConfirm: () => void;
}

export default function DeleteParticipantDialog({
  open,
  onClose,
  participantToDelete,
  isLoading = false,
  onConfirm,
}: DeleteParticipantDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogTitle>Delete Participant</DialogTitle>
        <div className="space-y-4">
          <div>
            Are you sure you want to delete{" "}
            <strong>
              {participantToDelete?.first_name} {participantToDelete?.last_name}
            </strong>
            ? This action cannot be undone.
          </div>
          <div className="flex gap-2">
            <Button onClick={onConfirm} variant="destructive" className="flex-1" disabled={isLoading}>
              {isLoading ? "Deleting..." : "Delete"}
            </Button>
            <Button onClick={onClose} variant="outline" className="flex-1" disabled={isLoading}>
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
