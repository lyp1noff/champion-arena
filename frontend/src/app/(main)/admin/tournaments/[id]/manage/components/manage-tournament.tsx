"use client";

import { useEffect, useState } from "react";
import { Bracket, BracketMatches, BracketType } from "@/lib/interfaces";
import { BracketView } from "@/components/bracket_view";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Command, CommandInput, CommandList, CommandEmpty, CommandItem } from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface Props {
  tournamentId: number;
  brackets: Bracket[];
  selectedBracket: Bracket | null;
  bracketMatches?: BracketMatches;
  loading: boolean;
  onSelectBracket: (bracket: Bracket) => Promise<void>;
  onSaveBracket: (updated: { id: number; type: BracketType; start_time: string; tatami: number }) => Promise<void>;
}

export default function ManageTournamentPage({
  tournamentId,
  brackets,
  selectedBracket,
  bracketMatches,
  loading,
  onSelectBracket,
  onSaveBracket,
}: Props) {
  const [open, setOpen] = useState(false);
  const [type, setType] = useState<BracketType>("single_elimination");
  const [startTime, setStartTime] = useState<string>("");
  const [tatami, setTatami] = useState<number | "">("");

  useEffect(() => {
    if (selectedBracket) {
      setType(selectedBracket.type || "single_elimination");
      setStartTime(selectedBracket.start_time || "");
      setTatami(selectedBracket.tatami ?? "");
    }
  }, [selectedBracket]);

  const handleSave = () => {
    if (!selectedBracket || !startTime || tatami === "") return;
    onSaveBracket({
      id: selectedBracket.id,
      type,
      start_time: startTime,
      tatami: Number(tatami),
    });
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 p-6 md:p-10 justify-center">
      {/* Preview */}
      {selectedBracket && (
        <Card className="flex-1 overflow-hidden">
          <div className="overflow-x-auto">
            <CardContent className="p-6">
              <BracketView
                loading={loading}
                matches={bracketMatches ?? []}
                bracket={selectedBracket}
                containerHeight={600}
              />
            </CardContent>
          </div>
        </Card>
      )}

      {/* Form */}
      <Card className="w-full md:w-[380px] shrink-0">
        <CardContent className="p-6 space-y-6">
          <h1 className="text-2xl font-bold">Manage Tournament #{tournamentId}</h1>

          {/* Bracket selection */}
          <div className="space-y-2">
            <Label>Bracket</Label>
            <Popover open={open} onOpenChange={setOpen}>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  role="combobox"
                  aria-expanded={open}
                  className="w-full block whitespace-normal text-left h-auto min-h-10"
                >
                  {selectedBracket ? selectedBracket.category : "Select a bracket..."}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[--radix-popover-trigger-width] p-0">
                <Command>
                  <CommandInput placeholder="Search brackets..." />
                  <CommandList>
                    <CommandEmpty>No brackets found.</CommandEmpty>
                    {brackets.map((bracket) => (
                      <CommandItem
                        key={bracket.id}
                        value={bracket.category}
                        onSelect={() => {
                          onSelectBracket(bracket);
                          setOpen(false);
                        }}
                      >
                        {bracket.category}
                      </CommandItem>
                    ))}
                  </CommandList>
                </Command>
              </PopoverContent>
            </Popover>
          </div>

          {/* Fields */}
          <div className="space-y-2">
            <Label>Type</Label>
            <Select value={type} onValueChange={(val) => setType(val as BracketType)}>
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="round_robin">Round Robin</SelectItem>
                <SelectItem value="single_elimination">Single Elimination</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Start Time</Label>
            <Input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              placeholder="Enter time (hh:mm)"
            />
          </div>

          <div className="space-y-2">
            <Label>Tatami</Label>
            <Input
              type="number"
              value={tatami}
              onChange={(e) => setTatami(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder="Enter tatami number"
            />
          </div>

          <Button className="w-full mt-6" onClick={handleSave} disabled={!selectedBracket || loading}>
            {loading ? "Saving..." : "Save"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
