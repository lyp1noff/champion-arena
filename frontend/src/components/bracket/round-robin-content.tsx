import { BracketMatches } from "@/lib/interfaces";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { getUniqueAthletes } from "@/lib/utils";

const TR_HEIGHT = undefined;

interface RoundRobinProps {
  bracketMatches: BracketMatches;
  containerHeight?: number;
}

export default function RoundRobinContent({ bracketMatches, containerHeight }: RoundRobinProps) {
  const athletes = getUniqueAthletes(bracketMatches);

  const content = (
    <ScrollArea className="flex-1 overflow-auto">
      <div className="overflow-auto">
        <table className="table-auto border-collapse text-sm">
          <thead>
            <tr style={{ height: TR_HEIGHT }}>
              <th className="border px-2 py-1 bg-muted"></th>
              {athletes.map((a) => (
                <th key={a.id} className="border px-2 py-1 bg-muted text-center font-normal text-xs">
                  {a.last_name} {a.first_name} ({a.coaches_last_name?.join(", ") || "No coach"})
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {athletes.map((rowAthlete) => (
              <tr key={rowAthlete.id} style={{ height: TR_HEIGHT }}>
                <td className="border px-2 py-1 bg-muted font-normal text-xs">
                  {rowAthlete.last_name} {rowAthlete.first_name} (
                  {rowAthlete.coaches_last_name?.join(", ") || "No coach"})
                </td>
                {athletes.map((colAthlete) => {
                  const isSame = rowAthlete.id === colAthlete.id;
                  return (
                    <td key={colAthlete.id} className="border px-2 py-1 text-center font-mono">
                      {(() => {
                        if (isSame) return "×";
                        return "";
                      })()}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ScrollBar orientation="horizontal" />
    </ScrollArea>
  );

  return containerHeight ? (
    <div className="flex" style={{ height: containerHeight }}>
      {content}
    </div>
  ) : (
    content
  );
}
