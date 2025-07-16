import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import React from "react";

interface UnsavedChangesDialogProps {
  open: boolean;
  onDiscard: () => void;
  onCancel: () => void;
}

export default function UnsavedChangesDialog({ open, onDiscard, onCancel }: UnsavedChangesDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onCancel}>
      <DialogContent className="max-w-xs">
        <DialogTitle>Unsaved Changes</DialogTitle>
        <div className="space-y-4">
          <div>You have unsaved changes. Discard changes and switch brackets?</div>
          <div className="flex gap-2">
            <Button onClick={onDiscard} className="flex-1" variant="destructive">
              Discard & Switch
            </Button>
            <Button onClick={onCancel} className="flex-1" variant="outline">
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
