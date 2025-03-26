"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { login } from "@/lib/api/auth";

export function useLoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await login({ username: email, password });
      toast.success("Welcome!");
      await router.push("/admin");
    } catch (err: unknown) {
      if (err instanceof Error) toast.error(err.message);
      else toast.error("Login failed");
    }
  };

  return {
    email,
    password,
    setEmail,
    setPassword,
    handleSubmit,
  };
}
