import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { Toaster } from "@/components/ui/sonner";
import { verifyTokenFromCookie } from "@/lib/auth";

export default async function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const payload = await verifyTokenFromCookie();

  return (
    <div className="relative flex flex-col min-h-screen">
      {/*<div className="absolute inset-0 bg-champion-pattern bg-repeat bg-[length:150px_150px] opacity-10 blur-sm" />*/}
      {/*<div className="relative z-10 flex flex-col min-h-screen">*/}
      <div className="relative z-10 flex flex-col min-h-screen">
        <Header user={payload} />
        <main className="flex-1">{children}</main>
        <Footer />
        <Toaster />
      </div>
    </div>
  );
}
