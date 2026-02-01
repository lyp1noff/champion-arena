import { z } from "zod";

export const createBracketSchema = z.object({
  category_id: z.string().min(1, "Category is required"),
  group_id: z.coerce.number().min(1, "Group must be at least 1"),
  type: z.enum(["single_elimination", "round_robin"]),
});

export type CreateBracketSchema = z.infer<typeof createBracketSchema>;

export const defaultBracketValues: CreateBracketSchema = {
  category_id: "",
  group_id: 1,
  type: "single_elimination",
};
