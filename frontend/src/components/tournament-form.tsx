"use client";

import { useEffect, useState } from "react";

import { useLocale } from "next-intl";

import { zodResolver } from "@hookform/resolvers/zod";
import { parseISO } from "date-fns";
import { CalendarIcon, Loader2 } from "lucide-react";
import type { DateRange } from "react-day-picker";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

import { uploadImage } from "@/lib/api/api";
import { createTournament, getTournamentById, importCbrFile, updateTournament } from "@/lib/api/tournaments";
import { formatDateToISO } from "@/lib/utils";

import { DateRange as DateRangeComponent } from "./date-range";

const formSchema = z
  .object({
    name: z.string().trim().min(3, { message: "Tournament name must be at least 3 characters." }),
    location: z.string().trim().min(3, { message: "Location must be at least 3 characters." }),
    tournament_range: z.object({
      from: z.date({ required_error: "Start date is required." }),
      to: z.date({ required_error: "End date is required." }),
    }),
    registration_range: z.object({
      from: z.date({ required_error: "Registration start date is required." }),
      to: z.date({ required_error: "Registration end date is required." }),
    }),
  })
  .refine((data) => data.tournament_range.to >= data.tournament_range.from, {
    message: "End date must be after start date",
    path: ["tournament_range.to"],
  })
  .refine((data) => data.registration_range.to >= data.registration_range.from, {
    message: "Registration end date must be after registration start date",
    path: ["registration_range.to"],
  })
  .refine((data) => data.tournament_range.from >= data.registration_range.to, {
    message: "Tournament must start after registration ends",
    path: ["tournament_range.from"],
  });

interface TournamentFormProps {
  tournamentId?: number;
  onSuccess?: () => void;
}

export function TournamentForm({ tournamentId, onSuccess }: TournamentFormProps) {
  const locale = useLocale();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [structureFile, setStructureFile] = useState<File | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      location: "",
      tournament_range: { from: new Date(), to: new Date() },
      registration_range: { from: new Date(), to: new Date() },
    },
  });

  useEffect(() => {
    if (tournamentId) {
      (async () => {
        try {
          const tournament = await getTournamentById(tournamentId);
          form.reset({
            name: tournament.name,
            location: tournament.location,
            tournament_range: {
              from: parseISO(tournament.start_date),
              to: parseISO(tournament.end_date),
            },
            registration_range: {
              from: parseISO(tournament.registration_start_date),
              to: parseISO(tournament.registration_end_date),
            },
          });
        } catch (err) {
          console.error(err);
          toast.error("Failed to load tournament data");
        }
      })();
    }
  }, [tournamentId, form]);

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    setIsSubmitting(true);
    try {
      let uploadedImageUrl = "";
      if (selectedImage) uploadedImageUrl = (await uploadImage(selectedImage, "champion/tournaments")) || "";

      const payload = {
        name: values.name,
        location: values.location,
        start_date: formatDateToISO(values.tournament_range.from),
        end_date: formatDateToISO(values.tournament_range.to),
        registration_start_date: formatDateToISO(values.registration_range.from),
        registration_end_date: formatDateToISO(values.registration_range.to),
        ...(uploadedImageUrl && { image_url: uploadedImageUrl }),
      };

      const result = tournamentId ? await updateTournament(tournamentId, payload) : await createTournament(payload);

      toast.success(tournamentId ? "Tournament updated" : "Tournament created");

      const finalId = tournamentId || result?.id;
      if (structureFile && finalId) {
        await importCbrFile(finalId, structureFile);
        toast.success("Structure file imported");
      }

      onSuccess?.();
    } catch (err) {
      console.error(err);
      toast.error("Error saving tournament");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        {/* Name & Location */}
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Tournament Name</FormLabel>
              <FormControl>
                <Input placeholder="Karate Junior Tournament" {...field} />
              </FormControl>
              <FormDescription>The official name of your tournament.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="location"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Location</FormLabel>
              <FormControl>
                <Input placeholder="Kyiv" {...field} />
              </FormControl>
              <FormDescription>Where the tournament will take place.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        {/* Date Ranges */}
        <div className="grid gap-6 sm:grid-cols-2">
          {(["registration_range", "tournament_range"] as const).map((name) => (
            <FormField
              key={name}
              control={form.control}
              name={name}
              render={({ field }) => (
                <FormItem className="flex flex-col">
                  <FormLabel>{name === "registration_range" ? "Registration Period" : "Tournament Dates"}</FormLabel>
                  <Popover>
                    <PopoverTrigger asChild>
                      <FormControl>
                        <Button
                          variant="outline"
                          className={`w-full pl-3 text-left font-normal ${
                            !field.value?.from && "text-muted-foreground"
                          }`}
                        >
                          {field.value?.from ? (
                            field.value.to ? (
                              <>
                                <DateRangeComponent start={field.value.from} end={field.value.to} locale={locale} />
                              </>
                            ) : (
                              <DateRangeComponent start={field.value.from} end={field.value.from} locale={locale} />
                            )
                          ) : (
                            <span>Select date range</span>
                          )}
                          <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                        </Button>
                      </FormControl>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="range"
                        selected={field.value as DateRange | undefined}
                        onSelect={field.onChange}
                        numberOfMonths={2}
                        weekStartsOn={1}
                        className="rounded-lg border shadow-sm"
                      />
                    </PopoverContent>
                  </Popover>
                  <FormMessage />
                </FormItem>
              )}
            />
          ))}
        </div>

        {/* Image & File Uploads */}
        <div>
          <label className="text-sm font-medium">Upload Tournament Image</label>
          <Input
            type="file"
            accept="image/*"
            className={"mt-2"}
            onChange={(e) => e.target.files?.[0] && setSelectedImage(e.target.files[0])}
          />
          <p className="mt-2 text-xs text-muted-foreground">Recommended size: 800x600px.</p>
        </div>

        <div>
          <label className="text-sm font-medium">Bracket Structure File (*.cbr)</label>
          <Input
            type="file"
            accept=".json,.cbr"
            className={"mt-2"}
            onChange={(e) => e.target.files?.[0] && setStructureFile(e.target.files[0])}
          />
        </div>

        <div className="flex justify-between">
          <Button type="button" variant="outline" onClick={() => onSuccess?.()}>
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {!tournamentId ? "Create Tournament" : "Update Tournament"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
