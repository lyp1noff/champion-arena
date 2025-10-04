import { Footer } from "@/components/footer";
import Script from "next/script";

export default function MainLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const analyticsUrl = process.env.NEXT_PUBLIC_ANALYTICS_URL;
  const analyticsId = process.env.NEXT_PUBLIC_ANALYTICS_ID;

  return (
    <>
      <main className="flex-1">{children}</main>
      <Footer />

      {analyticsUrl && analyticsId && (
        <Script src={analyticsUrl} data-website-id={analyticsId} strategy="afterInteractive" />
      )}
    </>
  );
}
