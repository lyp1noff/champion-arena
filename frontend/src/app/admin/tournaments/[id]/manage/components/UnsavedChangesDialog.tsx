import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import React from "react";

interface UnsavedChangesDialogProps {
  open: boolean;
  onDiscard: () => void;
  onCancel: () => void;
}

export default function UnsavedChangesDialog({ open, onDiscard, onCancel }: UnsavedChangesDialogProps) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-80">
        <CardHeader>
          <CardTitle>Unsaved Changes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>You have unsaved changes. Discard changes and switch brackets?</div>
          <div className="flex gap-2">
            <Button onClick={onDiscard} className="flex-1" variant="destructive">
              Discard & Switch
            </Button>
            <Button onClick={onCancel} className="flex-1" variant="outline">
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
