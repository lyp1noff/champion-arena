import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Bracket } from "@/lib/interfaces";
import { Label } from "@/components/ui/label";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from "@/components/ui/command";
import { ChevronsUpDown } from "lucide-react";
import React, { useState } from "react";

interface DeleteBracketDialogProps {
  open: boolean;
  onClose: () => void;
  bracketToDelete: Bracket | null;
  brackets: Bracket[];
  bracketToTransfer: Bracket | null;
  setBracketToTransfer: (id: Bracket | null) => void;
  onConfirm: () => void;
}

export default function DeleteBracketDialog({
  open,
  onClose,
  bracketToDelete,
  brackets,
  bracketToTransfer,
  setBracketToTransfer,
  onConfirm,
}: DeleteBracketDialogProps) {
  const [popoverOpen, setPopoverOpen] = useState(false);
  const selectedBracket = brackets.find((b) => b.id === bracketToTransfer?.id) || null;
  const filteredBrackets = bracketToDelete ? brackets.filter((b) => b.id !== bracketToDelete.id) : brackets;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogTitle>Delete Bracket</DialogTitle>
        {bracketToDelete && bracketToDelete.participants.length > 0 ? (
          <div className="space-y-4">
            <div>This bracket has participants. Please select a bracket to transfer them to before deleting.</div>
            <div className="space-y-2">
              <Label>Transfer to:</Label>
              <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
                <PopoverTrigger asChild>
                  <Button variant="outline" role="combobox" className="w-full justify-between">
                    {selectedBracket ? selectedBracket.display_name || selectedBracket.category : "Select bracket"}
                    <ChevronsUpDown className="ml-2 h-4 w-4 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-full p-0">
                  <Command>
                    <CommandInput placeholder="Search brackets..." />
                    <CommandList>
                      <CommandEmpty>No bracket found.</CommandEmpty>
                      <CommandGroup>
                        {filteredBrackets.map((bracket) => (
                          <CommandItem
                            key={bracket.id}
                            value={bracket.display_name || bracket.category}
                            onSelect={() => {
                              setBracketToTransfer(bracket);
                              setPopoverOpen(false);
                            }}
                          >
                            <div className="flex items-center gap-2">
                              {/* <div
                                className={`w-4 h-4 border rounded flex items-center justify-center ${transferTargetId === bracket.id ? "bg-primary border-primary" : "border-gray-300"}`}
                              >
                                {transferTargetId === bracket.id && (
                                  <span className="w-3 h-3 text-white flex items-center justify-center">
                                    <Check size={12} />
                                  </span>
                                )}
                              </div> */}
                              {bracket.display_name || bracket.category}
                            </div>
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>
            <div className="flex gap-2">
              <Button onClick={onConfirm} disabled={!bracketToTransfer} variant="destructive" className="flex-1">
                Transfer & Delete
              </Button>
              <Button onClick={onClose} className="flex-1" variant="outline">
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div>Are you sure you want to delete this empty bracket?</div>
            <div className="flex gap-2">
              <Button onClick={onConfirm} variant="destructive" className="flex-1">
                Delete
              </Button>
              <Button onClick={onClose} className="flex-1" variant="outline">
                Cancel
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
