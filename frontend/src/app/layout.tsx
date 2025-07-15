import { NextIntlClientProvider } from "next-intl";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { Header } from "@/components/header";
import { Toaster } from "@/components/ui/sonner";
import { verifyTokenFromCookie } from "@/lib/auth";
import "@/styles/globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"] });

export const metadata: Metadata = {
  title: "Champion",
  description: "Champion Tournament Management Platform",
};

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const payload = await verifyTokenFromCookie();
  return (
    <html lang="ua" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          <NextIntlClientProvider>
            <div className="relative flex flex-col min-h-screen">
              <div className="relative z-10 flex flex-col min-h-screen">
                <Header user={payload} />
                {children}
                <Toaster />
              </div>
            </div>
          </NextIntlClientProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
