"use client";

import { LoginForm } from "@/components/login-form";
import { useLoginForm } from "@/hooks/use-login-form";

export default function LoginPage() {
  const { email, password, setEmail, setPassword, handleSubmit } = useLoginForm();

  return (
    <main className="flex flex-1 items-center justify-center p-6 md:p-10">
      <div className="w-full max-w-sm">
        <LoginForm
          email={email}
          password={password}
          onEmailChange={setEmail}
          onPasswordChange={setPassword}
          onSubmit={handleSubmit}
        />
      </div>
    </main>
  );
}
