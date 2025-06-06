"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { format } from "date-fns";
import { ChevronsUpDown, Loader2 } from "lucide-react";
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
  coach_id: z.number({ required_error: "Please select a coach." }),
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
      coach_id: undefined,
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
          name="coach_id"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Coach</FormLabel>
              <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
                <PopoverTrigger asChild>
                  <FormControl>
                    <Button variant="outline" role="combobox" className="w-full justify-between">
                      {coaches.find((coach) => coach.id === field.value)?.last_name || "Select coach"}
                      <ChevronsUpDown className="ml-2 h-4 w-4 opacity-50" />
                    </Button>
                  </FormControl>
                </PopoverTrigger>
                <PopoverContent className="w-full p-0">
                  <Command>
                    <CommandInput placeholder="Search coach..." />
                    <CommandList>
                      <CommandEmpty>No coach found.</CommandEmpty>
                      <CommandGroup>
                        {coaches.map((coach) => (
                          <CommandItem
                            key={coach.id}
                            value={coach.last_name}
                            onSelect={() => {
                              form.setValue("coach_id", coach.id);
                              setIsPopoverOpen(false);
                            }}
                          >
                            {coach.last_name}
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
