"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Command, CommandInput, CommandList, CommandEmpty, CommandItem } from "@/components/ui/command";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { Bracket, BracketMatches, BracketType } from "@/lib/interfaces";
import { getTournamentBracketsById } from "@/lib/api/tournaments";
import { getBracketMatchesById, updateBracket } from "@/lib/api/brackets";
import { toast } from "sonner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { formatTimeToISO } from "@/lib/utils";
import { BracketView } from "@/components/bracket_view";

export default function ManageTournamentPage() {
  const { id } = useParams<{ id: string }>();

  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [bracketMatches, setBracketMatches] = useState<BracketMatches>();
  const [selectedBracket, setSelectedBracket] = useState<Bracket | null>(null);
  const [open, setOpen] = useState(false);

  const [type, setType] = useState<BracketType>("single_elimination");
  const [startTime, setStartTime] = useState<string>("");
  const [tatami, setTatami] = useState<number | "">("");

  const [loading, setLoading] = useState(false);

  async function fetchBracketMatches(bracket_id: number) {
    try {
      const data = await getBracketMatchesById(bracket_id);
      setBracketMatches(data);
    } catch (error) {
      console.error("Failed to fetch brackets:", error);
    }
  }

  useEffect(() => {
    async function fetchBrackets() {
      try {
        const data = await getTournamentBracketsById(Number(id));
        setBrackets(data);
      } catch (error) {
        console.error("Failed to fetch brackets:", error);
      }
    }

    fetchBrackets();
  }, [id]);

  const handleBracketSelect = async (bracket: Bracket) => {
    setLoading(true);
    setSelectedBracket(bracket);
    setType(bracket.type || "");
    setStartTime(bracket.start_time || "");
    setTatami(bracket.tatami ?? "");
    setOpen(false);
    await fetchBracketMatches(bracket.id);
    setLoading(false);
  };

  const handleSave = async () => {
    if (!selectedBracket) return;

    setLoading(true);
    try {
      const formattedStartTime = formatTimeToISO(startTime);
      if (!formattedStartTime || !tatami) {
        toast.error("Invalid start time format.");
        return;
      }

      await updateBracket(selectedBracket.id, {
        type,
        start_time: formattedStartTime,
        tatami: tatami,
      });

      const updatedBracket = {
        ...selectedBracket,
        type,
        start_time: formattedStartTime,
        tatami: tatami,
      };
      setSelectedBracket(updatedBracket);
      await fetchBracketMatches(selectedBracket.id);

      toast.success("Bracket saved successfully.");
    } catch (error) {
      console.error("Save error:", error);
      toast.error("Failed to save bracket.");
    } finally {
      setLoading(false);
    }
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
          <h1 className="text-2xl font-bold">Manage Tournament #{id}</h1>

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
                        onSelect={() => handleBracketSelect(bracket)}
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
            <Input type="time" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
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
