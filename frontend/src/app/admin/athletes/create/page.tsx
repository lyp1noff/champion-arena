"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { format } from "date-fns";
import { CalendarIcon, ChevronsUpDown, Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Calendar } from "@/components/ui/calendar";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { cn } from "@/lib/utils";

// Define the form schema with validation
const formSchema = z.object({
  last_name: z.string().min(2, {
    message: "Last name must be at least 2 characters.",
  }),
  first_name: z.string().min(2, {
    message: "First name must be at least 2 characters.",
  }),
  gender: z.string({
    required_error: "Please select a gender.",
  }),
  birth_date: z.date({
    required_error: "Birth date is required.",
  }),
  coach_id: z.number({
    required_error: "Please select a coach.",
  }),
});

// Coach type definition
type Coach = {
  id: number;
  name: string;
  specialty?: string;
};

export default function CreateAthletePage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [coaches, setCoaches] = useState<Coach[]>([]);
  const [isLoadingCoaches, setIsLoadingCoaches] = useState(true);

  // Initialize the form with default values
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      last_name: "",
      first_name: "",
      gender: "",
      birth_date: undefined,
      coach_id: undefined,
    },
  });

  // Fetch coaches from API
  useEffect(() => {
    const fetchCoaches = async () => {
      setIsLoadingCoaches(true);
      try {
        // In a real app, replace this with your actual API endpoint
        // const response = await fetch('/api/coaches')
        // const data = await response.json()

        // Simulating API response with mock data
        await new Promise((resolve) => setTimeout(resolve, 1000));
        const mockCoaches: Coach[] = [
          { id: 1, name: "John Smith", specialty: "Swimming" },
          { id: 2, name: "Maria Garcia", specialty: "Track & Field" },
          { id: 3, name: "David Johnson", specialty: "Basketball" },
          { id: 4, name: "Sarah Williams", specialty: "Tennis" },
          { id: 5, name: "Michael Brown", specialty: "Soccer" },
          { id: 6, name: "Jennifer Davis", specialty: "Gymnastics" },
          { id: 7, name: "Robert Miller", specialty: "Baseball" },
          { id: 8, name: "Lisa Wilson", specialty: "Volleyball" },
        ];

        setCoaches(mockCoaches);
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

  // Handle form submission
  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsSubmitting(true);

    try {
      // In a real app, you would send this data to your API
      console.log(values);

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      toast.success("Athlete created", {
        description: `${values.first_name} ${values.last_name} has been successfully added.`,
      });

      // Redirect to athletes list
      router.push("/admin/athletes");
    } catch (error) {
      console.error("Error creating athlete:", error);
      toast.error("Error", {
        description: "Failed to create athlete. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="container py-10">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="text-2xl">Add New Athlete</CardTitle>
          <CardDescription>Enter the athlete's information to add them to the system.</CardDescription>
        </CardHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <CardContent className="space-y-6">
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
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
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
                      <FormDescription>The athlete's gender identity.</FormDescription>
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
                      <Popover>
                        <PopoverTrigger asChild>
                          <FormControl>
                            <Button
                              variant={"outline"}
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
                            selected={field.value}
                            onSelect={field.onChange}
                            disabled={(date) => date > new Date()}
                            initialFocus
                          />
                        </PopoverContent>
                      </Popover>
                      <FormDescription>The athlete's date of birth.</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="coach_id"
                render={({ field }) => (
                  <FormItem className="flex flex-col">
                    <FormLabel>Coach</FormLabel>
                    <Popover>
                      <PopoverTrigger asChild>
                        <FormControl>
                          <Button
                            variant="outline"
                            role="combobox"
                            className={cn("w-full justify-between", !field.value && "text-muted-foreground")}
                            disabled={isLoadingCoaches}
                          >
                            {isLoadingCoaches ? (
                              <span className="flex items-center">
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Loading coaches...
                              </span>
                            ) : field.value ? (
                              coaches.find((coach) => coach.id === field.value)?.name || "Select coach"
                            ) : (
                              "Select coach"
                            )}
                            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
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
                                  value={coach.name}
                                  onSelect={() => {
                                    form.setValue("coach_id", coach.id, { shouldValidate: true });
                                  }}
                                >
                                  {coach.name}
                                </CommandItem>
                              ))}
                            </CommandGroup>
                          </CommandList>
                        </Command>
                      </PopoverContent>
                    </Popover>
                    <FormDescription>The coach responsible for this athlete.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
            <CardFooter className="flex justify-between">
              <Button type="button" variant="outline" onClick={() => router.push("/admin/athletes")}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting || isLoadingCoaches}>
                {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Add Athlete
              </Button>
            </CardFooter>
          </form>
        </Form>
      </Card>
    </div>
  );
}
