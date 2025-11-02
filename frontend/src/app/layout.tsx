import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getLocale } from "next-intl/server";
import { Inter } from "next/font/google";

import "@/styles/globals.css";

import { Header } from "@/components/header";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";

import { verifyTokenFromCookie } from "@/lib/auth";

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
  const locale = await getLocale();
  const payload = await verifyTokenFromCookie();
  return (
    <html lang={locale} suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
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
