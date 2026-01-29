"use client";

import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";

import { BRACKET_STATUS, Bracket } from "@/lib/interfaces";
import { getBracketDisplayName } from "@/lib/utils";

interface BracketHeaderProps {
  bracket: Bracket;
}

export function BracketHeader({ bracket }: BracketHeaderProps) {
  const title = getBracketDisplayName(bracket.category, bracket.group_id);
  const time = bracket.start_time?.slice(0, 5) ?? "-";
  const count = bracket.participants.length;
  const showStatus = bracket.status === BRACKET_STATUS.STARTED || bracket.status === BRACKET_STATUS.FINISHED;

  return (
    <>
      {/* Mobile */}
      <div className="flex w-full flex-col gap-1 md:hidden">
        <span className="text-base font-semibold group-hover:underline underline-offset-4">{title}</span>

        <div className="flex flex-row items-center w-full">
          <BracketMeta time={time} count={count} />
          {showStatus && <BracketStatus status={bracket.status} />}
        </div>
      </div>

      {/* Desktop */}
      <div className="hidden md:flex w-full flex-row items-center gap-4 justify-between">
        <span className="text-base font-semibold group-hover:underline underline-offset-4">{title}</span>

        <div className="flex gap-6 text-muted-foreground pr-4">
          {showStatus && <BracketStatus status={bracket.status} />}
          <span className="tabular-nums">{time}</span>
          <BracketCount count={count} />
        </div>
      </div>
    </>
  );
}

function BracketMeta({ time, count }: { time: string; count: number }) {
  return (
    <div className="flex gap-2 text-muted-foreground">
      <span className="tabular-nums">{time}</span>
      <span>|</span>
      <BracketCount count={count} />
    </div>
  );
}

function BracketCount({ count }: { count: number }) {
  const t = useTranslations("TournamentPage");
  return (
    <span className="tabular-nums">
      {t("participants")}: <span className="inline-block min-w-[3ch]">{count}</span>
    </span>
  );
}

function BracketStatus({ status }: { status: string }) {
  const t = useTranslations("TournamentPage");
  return <Badge variant={status === "started" ? "default" : "destructive"}>{t(status)}</Badge>;
}
