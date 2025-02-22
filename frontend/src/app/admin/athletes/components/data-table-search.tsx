import { Input } from "@/components/ui/input";

interface DataTablePaginationProps {
  search: string;
  setSearch: any;
  coachSearch: string;
  setCoachSearch: any;
}

export default function DataTablePagination({
  search,
  setSearch,
  coachSearch,
  setCoachSearch,
}: DataTablePaginationProps) {
  return (
    <div className="flex gap-4 mb-4">
      <Input placeholder="Search athlete..." value={search} onChange={(e) => setSearch(e.target.value.trim())} />
      <Input
        placeholder="Search coach..."
        value={coachSearch}
        onChange={(e) => setCoachSearch(e.target.value.trim())}
      />
    </div>
  );
}
