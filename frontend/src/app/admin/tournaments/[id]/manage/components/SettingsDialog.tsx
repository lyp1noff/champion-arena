import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Bracket, Category, BracketType } from "@/lib/interfaces";
import React from "react";

type SettingsForm = {
  type: BracketType;
  start_time: string;
  tatami: number | "";
  group_id: number;
  category_id: number;
};

interface SettingsDialogProps {
  open: boolean;
  onClose: () => void;
  settingsForm: SettingsForm;
  setSettingsForm: React.Dispatch<React.SetStateAction<SettingsForm>>;
  onSave: () => void;
  categories: Category[];
  selectedBracket: Bracket | null;
}

export default function SettingsDialog({
  open,
  onClose,
  settingsForm,
  setSettingsForm,
  onSave,
  categories,
  selectedBracket,
}: SettingsDialogProps) {
  if (!open || !selectedBracket) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-96">
        <CardHeader>
          <CardTitle>Edit Bracket Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Category</Label>
            <Select
              value={settingsForm.category_id?.toString() ?? ""}
              onValueChange={(val) => setSettingsForm((prev) => ({ ...prev, category_id: Number(val) }))}
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
          </div>
          <div className="space-y-2">
            <Label>Group</Label>
            <Input
              type="number"
              value={settingsForm.group_id}
              onChange={(e) => setSettingsForm((prev) => ({ ...prev, group_id: Number(e.target.value) }))}
              min="1"
            />
          </div>
          <div className="space-y-2">
            <Label>Type</Label>
            <Select
              value={settingsForm.type}
              onValueChange={(val) => setSettingsForm((prev) => ({ ...prev, type: val as BracketType }))}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
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
              value={settingsForm.start_time}
              onChange={(e) => setSettingsForm((prev) => ({ ...prev, start_time: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label>Tatami</Label>
            <Input
              type="number"
              value={settingsForm.tatami}
              onChange={(e) =>
                setSettingsForm((prev) => ({ ...prev, tatami: e.target.value === "" ? "" : Number(e.target.value) }))
              }
              min="1"
            />
          </div>
          <div className="flex gap-2">
            <Button onClick={onSave} className="flex-1">
              Save
            </Button>
            <Button variant="outline" onClick={onClose} className="flex-1">
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
