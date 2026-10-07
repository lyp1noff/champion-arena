"use client";

import { useCallback, useEffect, useState } from "react";
import { useAppRouter, useRouteParams } from "@/lib/router";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Athlete, Bracket, BracketMatch, Tournament } from "@/lib/interfaces";
import { getBrackets, getCurrentTournament, getMatches, getTournament } from "@/lib/api";
import {
  DEFAULT_MATCH_DURATION_MS,
  MATCH_DURATION_PRESETS,
  readDefaultMatchDuration,
  writeDefaultMatchDuration,
} from "@/lib/tatami-settings";
import { useI18n } from "@/lib/i18n";

export default function TatamiSetupPage() {
  const router = useAppRouter();
  const { t } = useI18n();

  const { id: tatamiId } = useRouteParams();

  const [tournament, setTournament] = useState<Tournament | null>(null);
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [matches, setMatches] = useState<BracketMatch[]>([]);
  const [selectedBracket, setSelectedBracket] = useState<string>("");
  const [selectedMatch, setSelectedMatch] = useState<BracketMatch | null>(null);
  const [defaultDurationMs, setDefaultDurationMs] = useState(DEFAULT_MATCH_DURATION_MS);
  const [loading, setLoading] = useState(false);
  const [selectedTournament, setSelectedTournament] = useState<number | null>(null);
  const [includeAllMatches, setIncludeAllMatches] = useState<boolean>(false);

  const getMatchStatusLabel = (status: string) => {
    if (status === "not_started") return t("match.notStarted");
    if (status === "started") return t("match.started");
    if (status === "finished") return t("match.finished");
    return status;
  };

  useEffect(() => {
    if (tatamiId) setDefaultDurationMs(readDefaultMatchDuration(tatamiId));
  }, [tatamiId]);

  // Load tournament and brackets on mount
  useEffect(() => {
    const fetchCurrentTournament = async () => {
      try {
        const data = await getCurrentTournament();
        setSelectedTournament(data.current_tournament_id);
      } catch (error) {
        console.error("Error fetching current tournament:", error);
      }
    };

    fetchCurrentTournament();
  }, []);

  useEffect(() => {
    const fetchTournament = async () => {
      try {
        const data = await getTournament(selectedTournament!.toString());
        setTournament(data);
      } catch (error) {
        console.error("Error fetching tournament:", error);
      }
    };

    const fetchBrackets = async () => {
      try {
        setLoading(true);
        const data = await getBrackets(selectedTournament!.toString());

        // Filter brackets assigned to this tatami
        const assignedBrackets = data
          .filter((bracket: Bracket) => bracket.tatami !== undefined && bracket.tatami !== null)
          .filter((bracket: Bracket) => String(bracket.tatami) === String(tatamiId))
          .sort((a, b) => {
            const dayA = a.day ?? 999;
            const dayB = b.day ?? 999;
            if (dayA !== dayB) return dayA - dayB;

            const timeA = a.start_time ?? "99:99:99";
            const timeB = b.start_time ?? "99:99:99";
            return timeA.localeCompare(timeB);
          });

        setBrackets(assignedBrackets);
      } catch (error) {
        console.error("Error fetching brackets:", error);
      } finally {
        setLoading(false);
      }
    };

    if (selectedTournament) {
      fetchTournament();
      fetchBrackets();
    }
  }, [selectedTournament, tatamiId]);

  const fetchMatches = useCallback(
    async (bracketId: string) => {
      try {
        setLoading(true);
        const data = await getMatches(bracketId);

        const validMatches = data.filter((bracketMatch: BracketMatch) => {
          if (includeAllMatches) {
            return true;
          }
          return (
            bracketMatch.match.athlete1 && bracketMatch.match.athlete2 && bracketMatch.match.status === "not_started"
          );
        });

        setMatches(validMatches);
      } catch (error) {
        console.error("Error fetching matches:", error);
      } finally {
        setLoading(false);
      }
    },
    [includeAllMatches],
  );

  useEffect(() => {
    if (selectedBracket) {
      fetchMatches(selectedBracket);
    }
  }, [fetchMatches, selectedBracket]);

  useEffect(() => {
    const saved = localStorage.getItem("selectedBracket");
    if (saved) {
      setSelectedBracket(saved);
      fetchMatches(saved);
    }

    const onStorage = (e: StorageEvent) => {
      if (e.key === "selectedBracket") {
        const v = e.newValue ?? "";
        setSelectedBracket(v);
        setSelectedMatch(null);
        setMatches([]);
        if (v) fetchMatches(v);
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [fetchMatches]);

  const handleBracketChange = (bracketId: string) => {
    setSelectedBracket(bracketId);
    setSelectedMatch(null);
    setMatches([]);

    if (bracketId) {
      localStorage.setItem("selectedBracket", bracketId);
      fetchMatches(bracketId);
    } else {
      localStorage.removeItem("selectedBracket");
    }
  };

  const handleIncludeAllMatchesChange = (checked: boolean) => {
    setIncludeAllMatches(checked as boolean);
  };

  const handleDefaultDurationChange = (durationMs: number) => {
    setDefaultDurationMs(durationMs);
    writeDefaultMatchDuration(tatamiId, durationMs);
  };

  const handleMatchChange = (matchId: string) => {
    const match = matches.find((m) => m.external_id === matchId);
    if (match) {
      setSelectedMatch(match);
    }
  };

  const getAthleteName = (athlete: Athlete) => {
    if (!athlete) return t("match.tbd");
    const coaches = Array.isArray(athlete.coaches_last_name)
      ? athlete.coaches_last_name.filter(Boolean).join(", ")
      : athlete.coaches_last_name;
    return `${athlete.last_name} ${athlete.first_name}${coaches ? ` (${coaches})` : ""}`;
  };

  const handleStartMatch = () => {
    if (!selectedMatch) {
      alert(t("tatami.selectMatchFirst"));
      return;
    }

    // TODO: Store match configuration in localStorage
    // const durationMs = (durationMinutes * 60 + durationSeconds) * 1000;
    const matchId = selectedMatch.match.external_id;

    // Navigate to the match control page
    router.push(`/admin/tatami/${tatamiId}/match/${matchId}`);
  };

  const selectedMatchData = matches.find((m) => m.external_id === selectedMatch?.external_id);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="tatami-setup-header">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{t("tatami.setupTitle", { id: tatamiId })}</h1>
            {tournament && <p className="text-gray-600">{t("tatami.tournament", { name: tournament.name })}</p>}
          </div>
          <a
            className="button button--outline button--default"
            href={`/screen/tatami/${tatamiId}`}
            target="_blank"
            rel="noopener noreferrer"
          >
            {t("tatami.openScreen")}
          </a>
        </div>

        <div className="flex flex-col gap-8">
          {/* Match Selection */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">{t("tatami.matchSelection")}</h2>

            <div className="space-y-4">
              {/* Bracket Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">{t("tatami.bracket")}</label>
                <Select value={selectedBracket} onValueChange={handleBracketChange}>
                  <SelectTrigger>
                    <SelectValue placeholder={t("tatami.selectBracket")} />
                  </SelectTrigger>
                  <SelectContent>
                    {brackets.map((bracket) => (
                      <SelectItem key={String(bracket.external_id)} value={String(bracket.external_id)}>
                        {t("tatami.day", { day: bracket.day ?? "-" })} - {bracket.start_time?.slice(0, 5) ?? "--:--"} - {bracket.display_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {brackets.length === 0 && !loading && (
                  <p className="text-sm text-red-600 mt-1">{t("tatami.noBrackets", { id: tatamiId })}</p>
                )}
              </div>

              {/* Match Selection */}
              {selectedBracket && (
                <div>
                  <label className="block text-sm font-medium mb-2">{t("tatami.match")}</label>
                  <Select value={selectedMatch?.external_id} onValueChange={(value) => handleMatchChange(value)}>
                    <SelectTrigger>
                      <SelectValue placeholder={t("tatami.selectMatch")} />
                    </SelectTrigger>
                    <SelectContent>
                      {matches.map((bracketMatch) => (
                        <SelectItem key={String(bracketMatch.external_id)} value={String(bracketMatch.external_id)}>
                          {t("tatami.matchOption", {
                            round: bracketMatch.round_number,
                            position: bracketMatch.position,
                            athlete1: bracketMatch.match.athlete1 ? getAthleteName(bracketMatch.match.athlete1) : t("common.unknown"),
                            athlete2: bracketMatch.match.athlete2 ? getAthleteName(bracketMatch.match.athlete2) : t("common.unknown"),
                          })}
                          {bracketMatch.match.status !== "not_started" && ` (${getMatchStatusLabel(bracketMatch.match.status)})`}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <div className="flex items-center space-x-2 mt-4">
                    <Checkbox
                      id="include-all-matches"
                      checked={includeAllMatches}
                      onCheckedChange={handleIncludeAllMatchesChange}
                    />
                    <label
                      htmlFor="include-all-matches"
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      {t("tatami.includeAll")}
                    </label>
                  </div>

                  {matches.length === 0 && !loading && (
                    <p className="text-sm text-red-600 mt-1">
                      {includeAllMatches
                        ? t("tatami.noMatches")
                        : t("tatami.noValidMatches")}
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Selected Match Info */}
            {selectedMatchData && (
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h3 className="font-medium mb-2">{t("tatami.selectedMatch")}:</h3>
                <div className="space-y-1 text-sm">
                  <div>
                    <strong>{t("tatami.round")}:</strong> {selectedMatchData.round_number}
                  </div>
                  <div>
                    <strong>{t("tatami.position")}:</strong> {selectedMatchData.position}
                  </div>
                  <div>
                    <strong>{t("common.status")}:</strong> {getMatchStatusLabel(selectedMatchData.match.status)}
                  </div>
                  <div>
                    <strong>{t("tatami.athlete1")}:</strong>{" "}
                    {selectedMatchData.match.athlete1 ? getAthleteName(selectedMatchData.match.athlete1) : t("common.unknown")}
                  </div>
                  <div>
                    <strong>{t("tatami.athlete2")}:</strong>{" "}
                    {selectedMatchData.match.athlete2 ? getAthleteName(selectedMatchData.match.athlete2) : t("common.unknown")}
                  </div>
                  {selectedMatchData.match.score_athlete1 !== undefined && (
                    <div>
                      <strong>{t("tatami.currentScore")}:</strong> {selectedMatchData.match.score_athlete1} -{" "}
                      {selectedMatchData.match.score_athlete2}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="duration-presets" role="group" aria-label={t("tatami.defaultTime")}>
              {MATCH_DURATION_PRESETS.map((preset) => (
                <Button
                  key={preset.durationMs}
                  variant={defaultDurationMs === preset.durationMs ? "default" : "outline"}
                  onClick={() => handleDefaultDurationChange(preset.durationMs)}
                >
                  {preset.label}
                </Button>
              ))}
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <Button onClick={handleStartMatch} disabled={!selectedMatch || loading} size="lg" className="px-8 mt-8 w-full">
          {loading ? t("common.loading") : t("tatami.startControl")}
        </Button>

        <Button
          onClick={() => router.push(`/admin/tatami/${tatamiId}/match/empty`)}
          size="lg"
          className="px-8 mt-8 w-full"
        >
          {t("tatami.startEmpty")}
        </Button>
      </div>
    </div>
  );
}
