import Link from "next/link";

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="w-full border-t py-4">
      <div className="container flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left">
        <div className="text-sm text-muted-foreground">© {currentYear} Andrii Paziuka. All rights reserved.</div>
        <div className="text-sm text-muted-foreground">
          <Link href="https://t.me/lyp1noff" className="font-medium underline underline-offset-4 hover:text-primary">
            @lyp1noff
          </Link>
        </div>
      </div>
    </footer>
  );
}
