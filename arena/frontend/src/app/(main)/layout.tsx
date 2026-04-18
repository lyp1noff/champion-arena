import Script from "next/script";

import { Footer } from "@/components/footer";

import { ANALYTICS_ID, ANALYTICS_URL } from "@/lib/config";

export default function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      <main className="flex-1">{children}</main>
      <Footer />

      {ANALYTICS_URL && ANALYTICS_ID && (
        <Script src={ANALYTICS_URL} data-website-id={ANALYTICS_ID} strategy="afterInteractive" />
      )}
    </>
  );
}
