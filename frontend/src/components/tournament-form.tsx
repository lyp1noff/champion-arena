"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { format, parseISO } from "date-fns";
import { CalendarIcon, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { uploadImage } from "@/lib/api/api";
import { formatDateToISO } from "@/lib/utils";
import { getTournamentById, createTournament, updateTournament, importCbrFile } from "@/lib/api/tournaments";

const formSchema = z
  .object({
    name: z.string().trim().min(3, { message: "Tournament name must be at least 3 characters." }),
    location: z.string().trim().min(3, { message: "Location must be at least 3 characters." }),
    start_date: z.date({ required_error: "Start date is required." }),
    end_date: z.date({ required_error: "End date is required." }),
    registration_start_date: z.date({ required_error: "Registration start date is required." }),
    registration_end_date: z.date({ required_error: "Registration end date is required." }),
  })
  .refine((data) => data.end_date >= data.start_date, {
    message: "End date must be after start date",
    path: ["end_date"],
  })
  .refine((data) => data.registration_end_date >= data.registration_start_date, {
    message: "Registration end date must be after registration start date",
    path: ["registration_end_date"],
  })
  .refine((data) => data.start_date >= data.registration_end_date, {
    message: "Tournament must start after registration ends",
    path: ["start_date"],
  });

const dateFields: (keyof z.infer<typeof formSchema>)[] = [
  "start_date",
  "end_date",
  "registration_start_date",
  "registration_end_date",
];

interface TournamentFormProps {
  tournamentId?: number;
  onSuccess?: () => void;
}

export function TournamentForm({ tournamentId, onSuccess }: TournamentFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [structureFile, setStructureFile] = useState<File | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      location: "",
      start_date: new Date(),
      end_date: new Date(),
      registration_start_date: new Date(),
      registration_end_date: new Date(),
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
            start_date: parseISO(tournament.start_date),
            end_date: parseISO(tournament.end_date),
            registration_start_date: parseISO(tournament.registration_start_date),
            registration_end_date: parseISO(tournament.registration_end_date),
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

      if (selectedImage) {
        uploadedImageUrl = (await uploadImage(selectedImage, "champion/tournaments")) || "";
      }

      let result;
      if (!tournamentId) {
        const payload = {
          ...values,
          start_date: formatDateToISO(values.start_date),
          end_date: formatDateToISO(values.end_date),
          registration_start_date: formatDateToISO(values.registration_start_date),
          registration_end_date: formatDateToISO(values.registration_end_date),
          image_url: uploadedImageUrl,
        };
        result = await createTournament(payload);
        toast.success("Tournament created");
      } else {
        const payload = {
          ...values,
          start_date: formatDateToISO(values.start_date),
          end_date: formatDateToISO(values.end_date),
          registration_start_date: formatDateToISO(values.registration_start_date),
          registration_end_date: formatDateToISO(values.registration_end_date),
          ...(uploadedImageUrl && { image_url: uploadedImageUrl }),
        };
        result = await updateTournament(tournamentId, payload);
        toast.success("Tournament updated");
      }

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
        <div className="space-y-6">
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

          {/* Dates */}
          <div className="grid gap-6 sm:grid-cols-2">
            {dateFields.map((name) => (
              <FormField
                key={name}
                control={form.control}
                name={name}
                render={({ field }) => (
                  <FormItem className="flex flex-col">
                    <FormLabel>{name.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl>
                          <Button
                            variant="outline"
                            className={`w-full pl-3 text-left font-normal ${!field.value && "text-muted-foreground"}`}
                          >
                            {field.value ? format(field.value, "PPP") : <span>Pick a date</span>}
                            <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                          </Button>
                        </FormControl>
                      </PopoverTrigger>
                      <PopoverContent className="w-auto p-0" align="start">
                        <Calendar
                          mode="single"
                          selected={field.value instanceof Date ? field.value : undefined}
                          onSelect={(date) => {
                            if (date) field.onChange(date);
                          }}
                          initialFocus
                        />
                      </PopoverContent>
                    </Popover>
                    <FormMessage />
                  </FormItem>
                )}
              />
            ))}
          </div>

          {/* Image */}
          <FormItem>
            <FormLabel>Upload Tournament Image</FormLabel>
            <FormControl>
              <Input
                type="file"
                accept="image/*"
                onChange={(e) => {
                  if (e.target.files?.length) {
                    setSelectedImage(e.target.files[0]);
                  }
                }}
              />
            </FormControl>
            <FormDescription>Recommended size: 800x600px.</FormDescription>
            <FormMessage />
          </FormItem>

          <FormItem>
            <FormLabel>Bracket Structure File (*.cbr)</FormLabel>
            <FormControl>
              <Input
                type="file"
                accept=".json,.cbr"
                onChange={(e) => {
                  if (e.target.files?.length) {
                    setStructureFile(e.target.files[0]);
                  }
                }}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
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
