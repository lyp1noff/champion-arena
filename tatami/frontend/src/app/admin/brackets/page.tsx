import Link from "next/link";

import { BracketAdmin } from "@/components/admin/bracket-admin";

export default function BracketsAdminPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex items-center justify-between">
          <Link href="/admin/setup" className="text-sm text-gray-600 underline-offset-4 hover:underline">
            Back to setup
          </Link>
        </div>
        <BracketAdmin />
      </div>
    </div>
  );
}
