import { BracketMatches } from "@/lib/interfaces";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { getUniqueAthletes } from "@/lib/utils";

const TR_HEIGHT = undefined;

interface RoundRobinProps {
  bracketMatches: BracketMatches;
  containerHeight?: number;
}

export default function RoundRobinContent({ bracketMatches, containerHeight }: RoundRobinProps) {
  const groups = new Map<number, BracketMatches>();

  for (const match of bracketMatches) {
    if (!groups.has(match.round_number)) groups.set(match.round_number, []);
    groups.get(match.round_number)!.push(match);
  }

  const content = (
    <ScrollArea className="flex-1 overflow-auto">
      <div className="flex flex-col gap-10">
        {Array.from(groups.entries()).map(([roundNumber, matches]) => {
          const athletes = getUniqueAthletes(matches);

          return (
            <div key={roundNumber}>
              <h2 className="text-lg font-bold mb-2">Group {roundNumber}</h2>
              <div className="overflow-auto">
                <table className="table-auto border-collapse text-sm">
                  <thead>
                    <tr style={{ height: TR_HEIGHT }}>
                      <th className="border px-2 py-1 bg-muted"></th>
                      {athletes.map((a) => (
                        <th key={a.id} className="border px-2 py-1 bg-muted text-center font-normal text-xs">
                          {a.last_name} {a.first_name} ({a.coach_last_name})
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {athletes.map((rowAthlete) => (
                      <tr key={rowAthlete.id} style={{ height: TR_HEIGHT }}>
                        <td className="border px-2 py-1 bg-muted font-normal text-xs">
                          {rowAthlete.last_name} {rowAthlete.first_name} ({rowAthlete.coach_last_name})
                        </td>
                        {athletes.map((colAthlete) => {
                          const isSame = rowAthlete.id === colAthlete.id;
                          // const hasMatch = matches.some(
                          //   (m) =>
                          //     (m.match.athlete1?.id === rowAthlete.id &&
                          //       m.match.athlete2?.id === colAthlete.id) ||
                          //     (m.match.athlete2?.id === rowAthlete.id &&
                          //       m.match.athlete1?.id === colAthlete.id)
                          // );
                          return (
                            <td key={colAthlete.id} className="border px-2 py-1 text-center font-mono">
                              {(() => {
                                if (isSame) return "×";
                                return "";
                                // const match = matches.find(
                                //   (m) =>
                                //     (m.match.athlete1?.id === rowAthlete.id &&
                                //       m.match.athlete2?.id === colAthlete.id) ||
                                //     (m.match.athlete2?.id === rowAthlete.id && m.match.athlete1?.id === colAthlete.id),
                                // );
                                //
                                // if (!match) return "";
                                //
                                // const { is_finished, score_athlete1, score_athlete2, athlete1 } = match.match;
                                //
                                // if (!is_finished) return "";
                                //
                                // const isNormalOrder = athlete1?.id === rowAthlete.id;
                                // const score1 = isNormalOrder ? score_athlete1 : score_athlete2;
                                // const score2 = isNormalOrder ? score_athlete2 : score_athlete1;
                                //
                                // return `${score1} : ${score2}`;
                              })()}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          );
        })}
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
