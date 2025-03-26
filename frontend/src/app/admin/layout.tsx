import { redirect } from "next/navigation";
import { verifyTokenFromCookie } from "@/lib/auth";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const payload = await verifyTokenFromCookie();

  if (!payload || payload.role !== "admin") {
    redirect("/login");
  }

  return <>{children}</>;
}
