import { LiveBadge } from "@/components/bracket/live-badge";
import { ParticipantNameWithMenu } from "@/components/bracket/participant-name-with-menu";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";

import { BracketMatches } from "@/lib/interfaces";
import { getUniqueAthletes } from "@/lib/utils";

const TR_HEIGHT = undefined;

interface RoundRobinProps {
  bracketMatches: BracketMatches;
}

function pairKey(a?: number, b?: number) {
  if (a == null || b == null) return "";
  return a < b ? `${a}-${b}` : `${b}-${a}`;
}

function EmptyCell() {
  return <td className="border px-2 py-1 text-center font-mono"></td>;
}

function SameAthleteCell() {
  return <td className="border px-2 py-1 text-center font-mono">×</td>;
}

function ScoreCell({ bm, rowId }: { bm: BracketMatches[number]; rowId: number }) {
  const status = bm.match.status;
  const s1 = bm.match.score_athlete1;
  const s2 = bm.match.score_athlete2;

  const rowIsAth1 = bm.match.athlete1?.id === rowId;
  const left = rowIsAth1 ? s1 : s2;
  const right = rowIsAth1 ? s2 : s1;

  const notStarted = status === "not_started";
  const scoreText = !notStarted ? `${left ?? 0} : ${right ?? 0}` : "";

  return (
    <td className="border px-2 py-1 font-mono whitespace-nowrap">
      <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto] items-center gap-1">
        <div className="justify-self-center text-center">{scoreText}</div>
        {status === "started" && <LiveBadge size="sm" className="justify-self-center sm:justify-self-end" />}
      </div>
    </td>
  );
}

export default function RoundRobinContent({ bracketMatches }: RoundRobinProps) {
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
      <div className="flex justify-center">
        <div className="overflow-auto">
          <table className="table-auto border-collapse text-sm">
            <thead>
              <tr style={{ height: TR_HEIGHT }}>
                <th className="border px-2 py-1 bg-muted"></th>
                {athletes.map((a) => (
                  <th key={a.id} className="border px-2 py-1 bg-muted text-center font-normal text-xs">
                    <ParticipantNameWithMenu participant={a} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {athletes.map((rowAthlete) => (
                <tr key={rowAthlete.id} style={{ height: TR_HEIGHT }}>
                  <td className="border px-2 py-1 bg-muted font-normal text-xs">
                    <ParticipantNameWithMenu participant={rowAthlete} />
                  </td>

                  {athletes.map((colAthlete) => {
                    if (rowAthlete.id === colAthlete.id) {
                      return <SameAthleteCell key={colAthlete.id} />;
                    }
                    const bm = matchByPair.get(pairKey(rowAthlete.id, colAthlete.id));
                    if (!bm) {
                      return <EmptyCell key={colAthlete.id} />;
                    }
                    return <ScoreCell key={colAthlete.id} bm={bm} rowId={rowAthlete.id} />;
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <ScrollBar orientation="horizontal" />
    </ScrollArea>
  );

  return content;
}
