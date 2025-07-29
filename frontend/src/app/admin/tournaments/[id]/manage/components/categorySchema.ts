import { z } from "zod";

export const createCategorySchema = z
  .object({
    name: z.string().min(1, "Name is required"),
    min_age: z.coerce.number().int().min(1, "Min age must be at least 1"),
    max_age: z.coerce.number().int().min(1, "Max age must be at least 1"),
    gender: z.enum(["male", "female"]),
  })
  .refine((data) => data.min_age <= data.max_age, {
    message: "Min age must be less than or equal to max age",
    path: ["max_age"],
  });

export type CreateCategorySchema = z.infer<typeof createCategorySchema>;
