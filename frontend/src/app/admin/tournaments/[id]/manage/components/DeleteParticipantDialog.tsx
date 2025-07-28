import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Participant } from "@/lib/interfaces";
import { deleteParticipant } from "@/lib/api/tournaments";
import { toast } from "sonner";
import { useState } from "react";

interface DeleteParticipantDialogProps {
  open: boolean;
  onClose: () => void;
  participantToDelete: Participant | null;
  onSuccess: () => void;
}

export default function DeleteParticipantDialog({
  open,
  onClose,
  participantToDelete,
  onSuccess,
}: DeleteParticipantDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleConfirm = async () => {
    if (!participantToDelete) return;

    setIsDeleting(true);
    try {
      await deleteParticipant(participantToDelete.id);
      toast.success("Participant deleted successfully");
      onSuccess();
      onClose();
    } catch {
      toast.error("Failed to delete participant");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCancel = () => {
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogTitle>Delete Participant</DialogTitle>
        <div className="space-y-4">
          <div>Are you sure you want to delete this participant? This action cannot be undone.</div>
          <div className="flex gap-2">
            <Button onClick={handleConfirm} variant="destructive" className="flex-1" disabled={isDeleting}>
              {isDeleting ? "Deleting..." : "Delete"}
            </Button>
            <Button onClick={handleCancel} className="flex-1" variant="outline" disabled={isDeleting}>
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
