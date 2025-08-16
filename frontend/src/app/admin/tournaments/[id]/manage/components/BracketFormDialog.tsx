import { Dialog, DialogContent, DialogTitle, DialogFooter, DialogHeader } from "@/components/ui/dialog";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Category } from "@/lib/interfaces";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import {
  createBracketSchema,
  CreateBracketSchema,
  defaultBracketValues,
} from "@/app/admin/tournaments/[id]/manage/components/bracketSchema";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import CreateCategoryDialog from "./CreateCategoryDialog";
import { createCategory } from "@/lib/api/brackets";

interface BracketFormDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: CreateBracketSchema) => Promise<void>;
  initialValues?: Partial<CreateBracketSchema>;
  categories: Category[];
  mode?: "create" | "edit";
  loadCategories: () => void;
}

export default function BracketFormDialog({
  open,
  onClose,
  onSubmit,
  initialValues = {},
  categories,
  mode = "create",
  loadCategories,
}: BracketFormDialogProps) {
  const [showCreateCategory, setShowCreateCategory] = useState(false);
  const [openCategoryPopover, setOpenCategoryPopover] = useState(false);

  const form = useForm<CreateBracketSchema>({
    resolver: zodResolver(createBracketSchema),
    defaultValues: {
      ...defaultBracketValues,
      ...initialValues,
    },
  });

  useEffect(() => {
    if (open) {
      form.reset({
        ...defaultBracketValues,
        ...initialValues,
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form, open]);

  const handleSubmit = async (data: CreateBracketSchema) => {
    await onSubmit(data);
    onClose();
  };

  return (
    <>
      <Dialog open={open} onOpenChange={onClose}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{mode === "edit" ? "Edit Bracket" : "Create New Bracket"}</DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="category_id"
                render={({ field }) => {
                  const selectedCategory = categories.find((c) => c.id.toString() === field.value);

                  return (
                    <FormItem>
                      <FormLabel>Category</FormLabel>
                      <Popover open={openCategoryPopover} onOpenChange={setOpenCategoryPopover}>
                        <PopoverTrigger asChild>
                          <FormControl>
                            <Button variant="outline" role="combobox" className="w-full justify-between">
                              {selectedCategory ? selectedCategory.name : "Select category"}
                              {/*<ChevronsUpDown className="ml-2 h-4 w-4 opacity-50" />*/}
                            </Button>
                          </FormControl>
                        </PopoverTrigger>
                        <PopoverContent className="w-full p-0">
                          <Command>
                            <CommandInput placeholder="Search categories..." />
                            <CommandList>
                              <CommandEmpty>No category found.</CommandEmpty>
                              <CommandGroup>
                                {categories.map((category) => (
                                  <CommandItem
                                    key={category.id}
                                    value={category.name + category.id}
                                    onSelect={() => {
                                      field.onChange(category.id.toString());
                                      setOpenCategoryPopover(false);
                                    }}
                                  >
                                    {category.name}
                                  </CommandItem>
                                ))}
                              </CommandGroup>
                            </CommandList>
                            <div className="border-t p-2">
                              <Button
                                variant="secondary"
                                className="w-full"
                                onClick={() => {
                                  setOpenCategoryPopover(false);
                                  setShowCreateCategory(true);
                                }}
                              >
                                Create New Category
                              </Button>
                            </div>
                          </Command>
                        </PopoverContent>
                      </Popover>
                      <FormMessage />
                    </FormItem>
                  );
                }}
              />

              <FormField
                control={form.control}
                name="group_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Group</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Bracket Type</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="single_elimination">Single Elimination</SelectItem>
                        <SelectItem value="round_robin">Round Robin</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="start_time"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Start Time</FormLabel>
                    <FormControl>
                      <Input type="time" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="tatami"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tatami</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter>
                <Button type="submit">{mode === "edit" ? "Save Changes" : "Create Bracket"}</Button>
                <Button type="button" variant="outline" onClick={onClose}>
                  Cancel
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
      <CreateCategoryDialog
        open={showCreateCategory}
        onClose={() => setShowCreateCategory(false)}
        onCreate={async (data) => {
          const created = await createCategory(data);
          loadCategories();
          form.setValue("category_id", created.id.toString());
        }}
      />
    </>
  );
}
