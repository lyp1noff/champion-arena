import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Admin() {
  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-4">Admin Page</h1>
      <div className="flex space-x-4">
        <Link href="/admin/tournaments">
          <Button>Tournaments</Button>
        </Link>
        <Link href="/admin/athletes">
          <Button>Athletes</Button>
        </Link>
      </div>
    </div>
  );
}
