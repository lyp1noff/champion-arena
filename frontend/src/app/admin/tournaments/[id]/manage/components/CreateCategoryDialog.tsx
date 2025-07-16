import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import React from "react";

type NewCategory = {
  name: string;
  age: string;
  gender: string;
};

interface CreateCategoryDialogProps {
  open: boolean;
  onClose: () => void;
  newCategory: NewCategory;
  setNewCategory: React.Dispatch<React.SetStateAction<NewCategory>>;
  onCreate: () => void;
}

export default function CreateCategoryDialog({
  open,
  onClose,
  newCategory,
  setNewCategory,
  onCreate,
}: CreateCategoryDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogTitle>Create New Category</DialogTitle>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Name</Label>
            <Input
              value={newCategory.name}
              onChange={(e) => setNewCategory((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="e.g., Men 18-25"
            />
          </div>
          <div className="space-y-2">
            <Label>Age</Label>
            <Input
              type="number"
              value={newCategory.age}
              onChange={(e) => setNewCategory((prev) => ({ ...prev, age: e.target.value }))}
              placeholder="e.g., 25"
            />
          </div>
          <div className="space-y-2">
            <Label>Gender</Label>
            <Select
              value={newCategory.gender}
              onValueChange={(val) => setNewCategory((prev) => ({ ...prev, gender: val }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="male">Male</SelectItem>
                <SelectItem value="female">Female</SelectItem>
                <SelectItem value="any">Any</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2">
            <Button onClick={onCreate} className="flex-1">
              Create
            </Button>
            <Button variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
