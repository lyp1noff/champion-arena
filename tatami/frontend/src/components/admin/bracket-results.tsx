import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { BracketMatch } from "@/lib/interfaces";
import { useI18n } from "@/lib/i18n";

interface BracketResultsProps {
  matches: BracketMatch[];
  loading: boolean;
  onCorrect: (match: BracketMatch, score1: number, score2: number, winnerId: number) => Promise<void>;
}

function athleteName(athlete: BracketMatch["match"]["athlete1"]): string {
  return athlete ? `${athlete.last_name} ${athlete.first_name}` : "—";
}

export function BracketResults({ matches, loading, onCorrect }: BracketResultsProps) {
  const { t } = useI18n();
  const finishedMatches = useMemo(() => matches.filter(({ match }) => match.status === "finished"), [matches]);
  const [selected, setSelected] = useState<BracketMatch | null>(null);
  const [score1, setScore1] = useState("0");
  const [score2, setScore2] = useState("0");
  const [winnerId, setWinnerId] = useState("");
  const [error, setError] = useState("");

  const openEditor = (bracketMatch: BracketMatch) => {
    setSelected(bracketMatch);
    setScore1(String(bracketMatch.match.score_athlete1 ?? 0));
    setScore2(String(bracketMatch.match.score_athlete2 ?? 0));
    setWinnerId(String(bracketMatch.match.winner_id ?? ""));
    setError("");
  };

  const closeEditor = () => {
    if (!loading) setSelected(null);
  };

  const save = async () => {
    if (!selected) return;
    const parsedScore1 = Number(score1);
    const parsedScore2 = Number(score2);
    const parsedWinnerId = Number(winnerId);
    if (![parsedScore1, parsedScore2, parsedWinnerId].every(Number.isInteger) || parsedScore1 < 0 || parsedScore2 < 0) {
      setError(t("brackets.resultInvalid"));
      return;
    }
    try {
      setError("");
      await onCorrect(selected, parsedScore1, parsedScore2, parsedWinnerId);
      setSelected(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : t("brackets.resultError"));
    }
  };

  return (
    <div className="admin-card bracket-results">
      <div className="admin-card__heading">
        <h2>{t("brackets.results")}</h2>
        <p>{t("brackets.resultsHint")}</p>
      </div>

      {finishedMatches.length ? (
        <div className="bracket-results__list">
          {finishedMatches.map((bracketMatch) => (
            <div className="bracket-results__row" key={bracketMatch.external_id}>
              <div className="bracket-results__meta">
                <strong>
                  {bracketMatch.match.stage === "repechage" ? t("brackets.repechage") : t("brackets.mainBracket")}
                  {` · ${t("brackets.roundPosition", { round: bracketMatch.round_number, position: bracketMatch.position })}`}
                </strong>
                <span>
                  {athleteName(bracketMatch.match.athlete1)} — {athleteName(bracketMatch.match.athlete2)}
                </span>
              </div>
              <div className="bracket-results__result">
                <strong>{bracketMatch.match.score_athlete1 ?? 0}:{bracketMatch.match.score_athlete2 ?? 0}</strong>
                <Button variant="outline" size="sm" onClick={() => openEditor(bracketMatch)}>
                  {t("brackets.editResult")}
                </Button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bracket-results__empty">{t("brackets.noFinishedMatches")}</div>
      )}

      <Dialog open={selected !== null} onOpenChange={(open) => !open && closeEditor()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t("brackets.editResult")}</DialogTitle>
            <DialogDescription>{t("brackets.editResultHint")}</DialogDescription>
          </DialogHeader>

          {selected ? (
            <div className="result-editor">
              <div className="result-editor__scores">
                <label>
                  <span>{athleteName(selected.match.athlete1)}</span>
                  <input className="admin-input" type="number" min="0" value={score1} onChange={(event) => setScore1(event.target.value)} />
                </label>
                <label>
                  <span>{athleteName(selected.match.athlete2)}</span>
                  <input className="admin-input" type="number" min="0" value={score2} onChange={(event) => setScore2(event.target.value)} />
                </label>
              </div>
              <label className="admin-field">
                <span>{t("match.winner")}</span>
                <select className="admin-input" value={winnerId} onChange={(event) => setWinnerId(event.target.value)}>
                  <option value="" disabled>{t("match.selectWinner")}</option>
                  {selected.match.athlete1 ? <option value={selected.match.athlete1.id}>{athleteName(selected.match.athlete1)}</option> : null}
                  {selected.match.athlete2 ? <option value={selected.match.athlete2.id}>{athleteName(selected.match.athlete2)}</option> : null}
                </select>
              </label>
              {error ? <div className="result-editor__error">{error}</div> : null}
            </div>
          ) : null}

          <DialogFooter>
            <Button variant="outline" onClick={closeEditor} disabled={loading}>{t("common.cancel")}</Button>
            <Button onClick={save} disabled={loading || !winnerId}>
              {loading ? t("common.loading") : t("common.save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
