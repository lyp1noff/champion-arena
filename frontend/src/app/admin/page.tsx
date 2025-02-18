import Link from "next/link";

export default function Admin() {
  return (
    <div className="container mx-auto py-10">
      <h1 className="text-3xl font-bold mb-4">Admin Page</h1>
      <Link href="/admin/athletes">Athletes</Link>
    </div>
  );
}
