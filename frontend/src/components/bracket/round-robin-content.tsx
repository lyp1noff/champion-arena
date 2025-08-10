import { BracketMatches } from "@/lib/interfaces";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { getUniqueAthletes } from "@/lib/utils";

const TR_HEIGHT = undefined;

interface RoundRobinProps {
  bracketMatches: BracketMatches;
  containerHeight?: number;
}

function pairKey(a?: number, b?: number) {
  if (a == null || b == null) return "";
  return a < b ? `${a}-${b}` : `${b}-${a}`;
}

export default function RoundRobinContent({ bracketMatches, containerHeight }: RoundRobinProps) {
  const athletes = getUniqueAthletes(bracketMatches);

  const matchByPair = new Map<string, (typeof bracketMatches)[number]>();
  for (const m of bracketMatches) {
    const id1 = m.match.athlete1?.id;
    const id2 = m.match.athlete2?.id;
    const key = pairKey(id1, id2);
    if (key) matchByPair.set(key, m);
  }

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

                  let cell = "×";
                  if (!isSame) {
                    const m = matchByPair.get(pairKey(rowAthlete.id, colAthlete.id));
                    if (m && m.match.ended_at) {
                      const { athlete1, score_athlete1, score_athlete2 } = m.match;
                      const rowIsAth1 = athlete1?.id === rowAthlete.id;
                      const left = rowIsAth1 ? score_athlete1 : m.match.score_athlete2;
                      const right = rowIsAth1 ? score_athlete2 : m.match.score_athlete1;
                      cell = `${left ?? ""} : ${right ?? ""}`;
                    } else {
                      cell = "";
                    }
                  }

                  return (
                    <td key={colAthlete.id} className="border px-2 py-1 text-center font-mono">
                      {cell}
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
