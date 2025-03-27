import { Header } from "@/components/header";
import { Footer } from "@/components/footer";
import { Toaster } from "@/components/ui/sonner";
import { verifyTokenFromCookie } from "@/lib/auth";

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const payload = await verifyTokenFromCookie();

  return (
    <div className="flex flex-col min-h-screen">
      <Header user={payload} />
      <main className="flex-1">{children}</main>
      <Footer />
      <Toaster />
    </div>
  );
}
