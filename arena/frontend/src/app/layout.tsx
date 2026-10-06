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
  applicationName: "Champion",
  manifest: "/site.webmanifest",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon.ico", sizes: "any", type: "image/x-icon" },
    ],
    apple: [{ url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" }],
  },
  appleWebApp: {
    capable: true,
    title: "Champion",
    statusBarStyle: "default",
  },
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
            <div className={"flex flex-col min-h-screen"}>
              <Header user={payload} />
              {children}
            </div>
            <Toaster />
          </NextIntlClientProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
