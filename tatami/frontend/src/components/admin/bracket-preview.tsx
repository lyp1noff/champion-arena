"use client";

import { useMemo } from "react";

import { Bracket, BracketMatch, Athlete } from "@/lib/interfaces";
import { useI18n } from "@/lib/i18n";

interface BracketPreviewProps {
  bracket: Bracket;
  matches: BracketMatch[];
  participantCount: number;
}

function athleteName(athlete?: Athlete): string {
  return athlete ? `${athlete.last_name} ${athlete.first_name}` : "";
}

function coachNames(athlete?: Athlete): string {
  if (!athlete?.coaches_last_name) return "";
  return Array.isArray(athlete.coaches_last_name)
    ? athlete.coaches_last_name.filter(Boolean).join(", ")
    : athlete.coaches_last_name;
}

function statusKey(status: BracketMatch["match"]["status"]): string {
  if (status === "started") return "match.started";
  if (status === "finished") return "match.finished";
  return "match.notStarted";
}

function roundLabel(matches: BracketMatch[], round: number, t: (key: string, params?: Record<string, string | number>) => string) {
  const type = matches.find((item) => item.match.round_type)?.match.round_type;
  if (type === "final") return t("brackets.final");
  if (type === "semifinal") return t("brackets.semifinal");
  if (type === "quarterfinal") return t("brackets.quarterfinal");
  return t("brackets.round", { round });
}

function ParticipantSlot({ athlete, score, winner, side }: {
  athlete?: Athlete;
  score?: number;
  winner: boolean;
  side: "red" | "blue";
}) {
  const { t } = useI18n();
  const coaches = coachNames(athlete);

  return (
    <div className={`bracket-preview__participant is-${side}${winner ? " is-winner" : ""}`}>
      <div className="bracket-preview__participant-text">
        <strong>{athleteName(athlete) || t("brackets.awaiting")}</strong>
        {coaches ? <span>{t("brackets.coach", { names: coaches })}</span> : null}
      </div>
      <span className="bracket-preview__score">{score ?? "—"}</span>
    </div>
  );
}

function PreviewMatchCard({ item, showTarget }: { item: BracketMatch; showTarget: boolean }) {
  const { t } = useI18n();
  const winnerId = item.match.winner_id;
  const hasTarget = showTarget && item.next_slot != null;

  return (
    <article className={`bracket-preview__match is-${item.match.status}`}>
      <header className="bracket-preview__match-header">
        <span>{t("brackets.match", { position: item.position })}</span>
        <span className={`bracket-preview__status is-${item.match.status}`}>{t(statusKey(item.match.status))}</span>
      </header>
      <ParticipantSlot
        athlete={item.match.athlete1}
        score={item.match.score_athlete1}
        winner={winnerId != null && winnerId === item.match.athlete1?.id}
        side="red"
      />
      <ParticipantSlot
        athlete={item.match.athlete2}
        score={item.match.score_athlete2}
        winner={winnerId != null && winnerId === item.match.athlete2?.id}
        side="blue"
      />
      {hasTarget ? (
        <footer>
          {t("brackets.advancesTo", {
            round: item.round_number + 1,
            position: Math.ceil(item.position / 2),
          })}
        </footer>
      ) : null}
    </article>
  );
}

function RoundColumns({ matches, repechage = false }: { matches: BracketMatch[]; repechage?: boolean }) {
  const { t } = useI18n();
  const rounds = useMemo(() => {
    const grouped = new Map<number, BracketMatch[]>();
    for (const item of matches) {
      const round = repechage ? (item.match.repechage_step ?? item.round_number) : item.round_number;
      grouped.set(round, [...(grouped.get(round) ?? []), item]);
    }
    return Array.from(grouped.entries())
      .map(([round, items]) => ({ round, items: items.sort((a, b) => a.position - b.position) }))
      .sort((a, b) => a.round - b.round);
  }, [matches, repechage]);

  const largestRound = Math.max(1, ...rounds.map(({ items }) => items.length));

  return (
    <div className="bracket-preview__scroll">
      <div className="bracket-preview__rounds">
        {rounds.map(({ round, items }, roundIndex) => (
          <section className="bracket-preview__round" key={round}>
            <h4>{repechage ? t("brackets.step", { step: round }) : roundLabel(items, round, t)}</h4>
            <ol className="bracket-preview__round-list" style={{ height: `${largestRound * 132}px` }}>
              {items.map((item) => (
                <li className={roundIndex < rounds.length - 1 ? "has-next" : ""} key={item.external_id}>
                  <PreviewMatchCard item={item} showTarget={!repechage} />
                </li>
              ))}
            </ol>
          </section>
        ))}
      </div>
    </div>
  );
}

function pairKey(first?: number, second?: number): string {
  if (first == null || second == null) return "";
  return first < second ? `${first}-${second}` : `${second}-${first}`;
}

function RoundRobinPreview({ bracket, matches }: Pick<BracketPreviewProps, "bracket" | "matches">) {
  const { t } = useI18n();
  const athletes = useMemo(() => {
    const result = new Map<number, Athlete>();
    for (const athlete of bracket.participants ?? []) result.set(athlete.id, athlete);
    for (const item of matches) {
      if (item.match.athlete1) result.set(item.match.athlete1.id, item.match.athlete1);
      if (item.match.athlete2) result.set(item.match.athlete2.id, item.match.athlete2);
    }
    return Array.from(result.values());
  }, [bracket.participants, matches]);

  const matchByPair = new Map<string, BracketMatch>();
  for (const item of matches) {
    const key = pairKey(item.match.athlete1?.id, item.match.athlete2?.id);
    if (key) matchByPair.set(key, item);
  }

  return (
    <div className="bracket-preview__scroll">
      <table className="round-robin-preview">
        <thead>
          <tr>
            <th>#</th>
            {athletes.map((athlete, index) => <th key={athlete.id}>{index + 1}</th>)}
          </tr>
        </thead>
        <tbody>
          {athletes.map((rowAthlete, rowIndex) => (
            <tr key={rowAthlete.id}>
              <th>
                <span>{rowIndex + 1}. {athleteName(rowAthlete)}</span>
                {coachNames(rowAthlete) ? <small>{t("brackets.coach", { names: coachNames(rowAthlete) })}</small> : null}
              </th>
              {athletes.map((columnAthlete) => {
                if (rowAthlete.id === columnAthlete.id) return <td className="is-self" key={columnAthlete.id}>×</td>;
                const item = matchByPair.get(pairKey(rowAthlete.id, columnAthlete.id));
                if (!item) return <td key={columnAthlete.id}>—</td>;
                const rowIsFirst = item.match.athlete1?.id === rowAthlete.id;
                const ownScore = rowIsFirst ? item.match.score_athlete1 : item.match.score_athlete2;
                const opponentScore = rowIsFirst ? item.match.score_athlete2 : item.match.score_athlete1;
                const won = item.match.winner_id === rowAthlete.id;
                return (
                  <td className={`is-${item.match.status}${won ? " is-winner" : ""}`} key={columnAthlete.id} title={t(statusKey(item.match.status))}>
                    {item.match.status === "not_started" ? "—" : `${ownScore ?? 0}:${opponentScore ?? 0}`}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function BracketPreview({ bracket, matches, participantCount }: BracketPreviewProps) {
  const { t } = useI18n();
  const mainMatches = matches.filter((item) => item.match.stage !== "repechage");
  const repechageMatches = matches.filter((item) => item.match.stage === "repechage");
  const repechageSides = Array.from(new Set(repechageMatches.map((item) => item.match.repechage_side ?? "—")))
    .sort()
    .map((side) => ({
      side,
      matches: repechageMatches.filter((item) => (item.match.repechage_side ?? "—") === side),
    }));
  const bracketStatus = bracket.status === "finished"
    ? t("brackets.statusFinished")
    : bracket.status === "started"
      ? t("brackets.statusStarted")
      : t("brackets.statusPending");

  return (
    <div className="admin-card bracket-preview">
      <div className="bracket-preview__heading">
        <div>
          <h2>{t("brackets.preview")}</h2>
          <p>{t("brackets.previewHint")}</p>
        </div>
        <div className="bracket-preview__meta">
          <span>{t("brackets.athleteCount", { count: participantCount })}</span>
          <span>{bracketStatus}</span>
          <span>{bracket.type === "round_robin" ? t("brackets.typeRoundRobin") : t("brackets.typeSingle")}</span>
          {bracket.day != null ? <span>{t("brackets.day", { day: bracket.day })}</span> : null}
          {bracket.tatami != null ? <span>{t("common.tatami", { id: bracket.tatami })}</span> : null}
          {bracket.start_time ? <span>{bracket.start_time.slice(0, 5)}</span> : null}
        </div>
      </div>

      {!matches.length ? (
        <div className="bracket-preview__empty">{t("brackets.noMatches")}</div>
      ) : bracket.type === "round_robin" ? (
        <RoundRobinPreview bracket={bracket} matches={matches} />
      ) : (
        <div className="bracket-preview__sections">
          <section>
            <h3>{t("brackets.mainBracket")}</h3>
            <RoundColumns matches={mainMatches} />
          </section>
          {repechageSides.map(({ side, matches: sideMatches }) => (
            <section key={side}>
              <h3>{t("brackets.repechageSide", { side })}</h3>
              <RoundColumns matches={sideMatches} repechage />
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
