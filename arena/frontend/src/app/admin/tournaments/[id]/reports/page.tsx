"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useTranslations } from "next-intl";
import { useParams } from "next/navigation";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { getTournamentBracketsById, getTournamentMatchesFullById } from "@/lib/api/tournaments";
import { Bracket, BracketMatchAthlete, BracketMatchesFull } from "@/lib/interfaces";
import { getBracketDisplayName } from "@/lib/utils";

type ReportType = "kids_by_coach" | "fights_by_bracket" | "participants_by_bracket";

const athleteNameWithCoaches = (athlete: BracketMatchAthlete | null, fallback: string) => {
  if (!athlete) return fallback;
  const name = `${athlete.last_name} ${athlete.first_name}`.trim();
  const coaches = athlete.coaches_last_name?.length ? athlete.coaches_last_name.join(", ") : "";
  return coaches ? `${name} (${coaches})` : name;
};

export default function TournamentReportsPage() {
  const t = useTranslations("AdminTournaments");
  const params = useParams<{ id?: string }>();
  const tournamentId = Number(params?.id);
  const [reportType, setReportType] = useState<ReportType>("kids_by_coach");
  const [reportText, setReportText] = useState("");
  const [brackets, setBrackets] = useState<Bracket[]>([]);
  const [matchesFull, setMatchesFull] = useState<BracketMatchesFull[]>([]);
  const [loading, setLoading] = useState(false);

  const reportTemplates = useMemo(
    () => ({
      kids_by_coach: t("reportTemplateKidsByCoach"),
      fights_by_bracket: t("reportTemplateFightsByBracket"),
      participants_by_bracket: t("reportTemplateParticipantsByBracket"),
    }),
    [t],
  );

  useEffect(() => {
    if (!tournamentId) return;
    setLoading(true);
    setReportText(t("reportLoading"));
    Promise.all([getTournamentBracketsById(tournamentId, true), getTournamentMatchesFullById(tournamentId)])
      .then(([bracketsData, matchesData]) => {
        setBrackets(bracketsData);
        setMatchesFull(matchesData);
      })
      .catch((error) => {
        console.error("Failed to load report data:", error);
        toast.error(t("reportLoadError"));
        setReportText(reportTemplates[reportType]);
      })
      .finally(() => setLoading(false));
  }, [reportTemplates, reportType, t, tournamentId]);

  const buildKidsByCoach = useCallback(
    (source: Bracket[]) => {
      if (!source.length) return t("reportEmpty");
      const coachMap = new Map<string, Map<number, string>>();
      const unknownCoach = t("reportCoachUnknown");

      source.forEach((bracket) => {
        bracket.participants.forEach((participant) => {
          const coaches = participant.coaches_last_name?.length ? participant.coaches_last_name : [unknownCoach];
          const name = `${participant.last_name} ${participant.first_name}`.trim();
          coaches.forEach((coach) => {
            const key = coach || unknownCoach;
            if (!coachMap.has(key)) coachMap.set(key, new Map());
            coachMap.get(key)?.set(participant.athlete_id, name);
          });
        });
      });

      if (!coachMap.size) return t("reportEmpty");

      return Array.from(coachMap.entries())
        .sort(([a], [b]) => a.localeCompare(b, "ru"))
        .map(([coach, athletes]) => {
          const athleteLines = Array.from(athletes.values())
            .sort((a, b) => a.localeCompare(b, "ru"))
            .map((name) => `- ${name}`)
            .join("\n");
          return `${t("reportCoachLabel")}: ${coach} (${athletes.size})\n${athleteLines}`;
        })
        .join("\n\n");
    },
    [t],
  );

  const buildParticipantsByBracket = useCallback(
    (source: Bracket[]) => {
      if (!source.length) return t("reportEmpty");
      return source
        .map((bracket) => {
          const title = bracket.display_name ?? getBracketDisplayName(bracket.category, bracket.group_id);
          const participants = bracket.participants
            .slice()
            .sort((a, b) => a.seed - b.seed)
            .map((participant) => `- ${participant.last_name} ${participant.first_name}`.trim())
            .join("\n");
          return `${title}\n${participants || t("reportEmpty")}`;
        })
        .join("\n\n");
    },
    [t],
  );

  const buildFightsByBracket = useCallback(
    (source: BracketMatchesFull[]) => {
      if (!source.length) return t("reportEmpty");
      const tbd = t("reportAthleteTbd");
      return source
        .map((bracket) => {
          const title = bracket.display_name ?? getBracketDisplayName(bracket.category, bracket.group_id);
          const fights = bracket.matches
            .map((match, index) => {
              const left = athleteNameWithCoaches(match.match.athlete1, tbd);
              const right = athleteNameWithCoaches(match.match.athlete2, tbd);
              return `${index + 1}) ${left} vs ${right}`;
            })
            .join("\n");
          return `${title}\n${fights || t("reportEmpty")}`;
        })
        .join("\n\n");
    },
    [t],
  );

  useEffect(() => {
    if (!tournamentId) return;
    if (!brackets.length && !matchesFull.length) {
      setReportText(reportTemplates[reportType]);
      return;
    }

    if (reportType === "kids_by_coach") {
      setReportText(buildKidsByCoach(brackets));
      return;
    }

    if (reportType === "participants_by_bracket") {
      setReportText(buildParticipantsByBracket(brackets));
      return;
    }

    setReportText(buildFightsByBracket(matchesFull));
  }, [
    brackets,
    matchesFull,
    reportTemplates,
    reportType,
    tournamentId,
    buildFightsByBracket,
    buildKidsByCoach,
    buildParticipantsByBracket,
  ]);

  const handleCopy = async () => {
    if (!reportText.trim()) {
      toast.error(t("reportCopyError"));
      return;
    }
    try {
      const canClipboard = typeof navigator !== "undefined" && navigator.clipboard?.writeText;
      if (canClipboard) {
        await navigator.clipboard.writeText(reportText);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = reportText;
        textarea.setAttribute("readonly", "true");
        textarea.style.position = "absolute";
        textarea.style.left = "-9999px";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      toast.success(t("reportCopied"));
    } catch (error) {
      console.error("Failed to copy report:", error);
      toast.error(t("reportCopyError"));
    }
  };

  return (
    <div className="container h-full flex-1 flex-col p-8 md:flex">
      <Card className="mx-auto w-full max-w-4xl">
        <CardHeader>
          <CardTitle>{t("reportsTitle")}</CardTitle>
          <CardDescription>{t("reportsDescription")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="report-type">{t("reportSelectLabel")}</Label>
            <Select value={reportType} onValueChange={(value) => setReportType(value as ReportType)}>
              <SelectTrigger id="report-type">
                <SelectValue placeholder={t("reportSelectPlaceholder")} />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="kids_by_coach">{t("reportKidsByCoach")}</SelectItem>
                <SelectItem value="fights_by_bracket">{t("reportFightsByBracket")}</SelectItem>
                <SelectItem value="participants_by_bracket">{t("reportParticipantsByBracket")}</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="report-text">{t("reportTextLabel")}</Label>
            <textarea
              id="report-text"
              className="min-h-[260px] w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              value={reportText}
              onChange={(event) => setReportText(event.target.value)}
            />
          </div>

          <div className="flex flex-wrap justify-end gap-2">
            <Button onClick={handleCopy} disabled={loading}>
              {t("reportCopy")}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
