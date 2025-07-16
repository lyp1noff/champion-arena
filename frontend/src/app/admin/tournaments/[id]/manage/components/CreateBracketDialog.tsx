import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Category, BracketType } from "@/lib/interfaces";
import React from "react";

type NewBracket = {
  category_id: string;
  group_id: number;
  type: BracketType;
  start_time: string;
  tatami: string;
};

interface CreateBracketDialogProps {
  open: boolean;
  onClose: () => void;
  newBracket: NewBracket;
  setNewBracket: React.Dispatch<React.SetStateAction<NewBracket>>;
  onCreate: () => void;
  categories: Category[];
  onShowCreateCategory: () => void;
}

export default function CreateBracketDialog({
  open,
  onClose,
  newBracket,
  setNewBracket,
  onCreate,
  categories,
  onShowCreateCategory,
}: CreateBracketDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogTitle>Create New Bracket</DialogTitle>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Category</Label>
            <Select
              value={newBracket.category_id}
              onValueChange={(val) => setNewBracket((prev) => ({ ...prev, category_id: val }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {categories.map((category: Category) => (
                  <SelectItem key={category.id} value={category.id.toString()}>
                    {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm" onClick={onShowCreateCategory}>
              New Category
            </Button>
          </div>
          <div className="space-y-2">
            <Label>Group</Label>
            <Input
              type="number"
              value={newBracket.group_id}
              onChange={(e) => setNewBracket((prev) => ({ ...prev, group_id: Number(e.target.value) }))}
              min="1"
            />
          </div>
          <div className="space-y-2">
            <Label>Type</Label>
            <Select
              value={newBracket.type}
              onValueChange={(val) => setNewBracket((prev) => ({ ...prev, type: val as BracketType }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="single_elimination">Single Elimination</SelectItem>
                <SelectItem value="round_robin">Round Robin</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Start Time</Label>
            <Input
              type="time"
              value={newBracket.start_time}
              onChange={(e) => setNewBracket((prev) => ({ ...prev, start_time: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label>Tatami</Label>
            <Input
              type="number"
              value={newBracket.tatami}
              onChange={(e) => setNewBracket((prev) => ({ ...prev, tatami: e.target.value }))}
              min="1"
            />
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
