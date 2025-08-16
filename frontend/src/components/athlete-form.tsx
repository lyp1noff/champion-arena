"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { format } from "date-fns";
import { ChevronsUpDown, Loader2, Check } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { getCoaches } from "@/lib/api/api";
import { createAthlete } from "@/lib/api/athletes";
import { Athlete, Coach } from "@/lib/interfaces";

const formSchema = z.object({
  last_name: z.string().min(2, { message: "Last name must be at least 2 characters." }),
  first_name: z.string().min(2, { message: "First name must be at least 2 characters." }),
  gender: z.string().nonempty({ message: "Please select a gender." }),
  birth_date: z.string().nonempty({ message: "Birth date is required." }),
  coaches_id: z.array(z.number()).default([]),
});

interface AthleteFormProps {
  defaultValues?: Partial<z.infer<typeof formSchema>>;
  onSubmit?: (values: z.infer<typeof formSchema>) => Promise<void>;
  onSuccess?: (athlete: Athlete) => void;
  onCancel?: () => void;
}

export default function AthleteForm({ defaultValues, onSubmit, onSuccess, onCancel }: AthleteFormProps) {
  const [coaches, setCoaches] = useState<Coach[]>([]);
  const [isLoadingCoaches, setIsLoadingCoaches] = useState(true);
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: defaultValues ?? {
      last_name: "",
      first_name: "",
      gender: "",
      birth_date: "",
      coaches_id: [],
    },
  });

  useEffect(() => {
    const fetchCoaches = async () => {
      setIsLoadingCoaches(true);
      try {
        const data = await getCoaches();
        setCoaches(data);
      } catch (error) {
        console.error("Error fetching coaches:", error);
        toast.error("Failed to load coaches", {
          description: "Please try again or contact support.",
        });
      } finally {
        setIsLoadingCoaches(false);
      }
    };

    fetchCoaches();
  }, []);

  const handleSubmitInternal = async (values: z.infer<typeof formSchema>) => {
    setSubmitting(true);
    try {
      if (onSubmit) {
        await onSubmit(values);
      } else {
        const athlete = await createAthlete(values);
        onSuccess?.(athlete);
      }
    } catch {
      toast.error("Failed to submit athlete");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmitInternal)} className="space-y-6">
        <div className="grid gap-6 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="first_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>First Name</FormLabel>
                <FormControl>
                  <Input placeholder="Enter first name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="last_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Last Name</FormLabel>
                <FormControl>
                  <Input placeholder="Enter last name" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className="grid gap-6 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="gender"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Gender</FormLabel>
                <Select onValueChange={field.onChange}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select gender" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="male">Male</SelectItem>
                    <SelectItem value="female">Female</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="birth_date"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Birth Date</FormLabel>
                <FormControl>
                  <Input
                    type="date"
                    className="block w-full"
                    value={field.value}
                    onChange={(e) => field.onChange(e.target.value)}
                    max={format(new Date(), "yyyy-MM-dd")}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <FormField
          control={form.control}
          name="coaches_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Coaches</FormLabel>
              <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
                <PopoverTrigger asChild>
                  <FormControl>
                    <Button variant="outline" role="combobox" className="w-full justify-between">
                      {field.value.length > 0
                        ? `${field.value.length} coach${field.value.length > 1 ? "es" : ""} selected`
                        : "Select coaches"}
                      <ChevronsUpDown className="ml-2 h-4 w-4 opacity-50" />
                    </Button>
                  </FormControl>
                </PopoverTrigger>
                <PopoverContent className="w-full p-0">
                  <Command>
                    <CommandInput placeholder="Search coaches..." />
                    <CommandList>
                      <CommandEmpty>No coach found.</CommandEmpty>
                      <CommandGroup>
                        {coaches.map((coach) => (
                          <CommandItem
                            key={coach.id}
                            value={coach.last_name}
                            onSelect={() => {
                              const currentCoaches = field.value || [];
                              const coachIndex = currentCoaches.indexOf(coach.id);

                              if (coachIndex > -1) {
                                // Remove coach if already selected
                                const newCoaches = currentCoaches.filter((id) => id !== coach.id);
                                form.setValue("coaches_id", newCoaches);
                              } else {
                                // Add coach if not selected
                                form.setValue("coaches_id", [...currentCoaches, coach.id]);
                              }
                            }}
                          >
                            <div className="flex items-center gap-2">
                              <div
                                className={`w-4 h-4 border rounded flex items-center justify-center ${field.value?.includes(coach.id) ? "bg-primary border-primary" : "border-gray-300"}`}
                              >
                                {field.value?.includes(coach.id) && (
                                  <span className="w-3 h-3 text-white flex items-center justify-center">
                                    <Check size={12} />
                                  </span>
                                )}
                              </div>
                              {coach.last_name}
                            </div>
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-between">
          <Button type="button" variant="outline" onClick={onCancel ?? (() => history.back())}>
            Cancel
          </Button>
          <Button type="submit" disabled={submitting || isLoadingCoaches}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {defaultValues?.last_name ? "Save Changes" : "Add Athlete"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
