"use client";

import { useTranslations } from "next-intl";

import { Badge } from "@/components/ui/badge";

// import { BracketCount } from "@/app/(main)/tournaments/[id]/components/BracketCount";
// import { BracketMeta } from "@/app/(main)/tournaments/[id]/components/BracketMeta";
// import { BracketStatus } from "@/app/(main)/tournaments/[id]/components/BracketStatus";

import { Bracket } from "@/lib/interfaces";
import { getBracketDisplayName } from "@/lib/utils";

interface BracketHeaderProps {
  bracket: Bracket;
}

export function BracketHeader({ bracket }: BracketHeaderProps) {
  const t = useTranslations("TournamentPage");

  const title = getBracketDisplayName(bracket.category, bracket.group_id);
  const time = bracket.start_time?.slice(0, 5) ?? "-";
  const count = bracket.participants.length;
  const showStatus = ["started", "finished"].includes(bracket.status);

  return (
    <>
      {/* Mobile */}
      <div className="flex w-full flex-col gap-1 sm:hidden">
        <span className="text-base font-semibold group-hover:underline underline-offset-4">{title}</span>

        <div className="flex flex-row items-center w-full">
          <BracketMeta time={time} count={count} t={t} />
          {showStatus && <BracketStatus status={bracket.status} t={t} />}
        </div>
      </div>

      {/* Desktop */}
      <div className="hidden sm:flex w-full flex-row items-center gap-4 justify-between">
        <span className="text-base font-semibold group-hover:underline underline-offset-4">{title}</span>

        <div className="flex gap-6 text-muted-foreground pr-4">
          {showStatus && <BracketStatus status={bracket.status} t={t} />}
          <span className="tabular-nums">{time}</span>
          <BracketCount count={count} t={t} />
        </div>
      </div>
    </>
  );
}

function BracketMeta({ time, count, t }: { time: string; count: number; t: any }) {
  return (
    <div className="flex gap-2 text-muted-foreground">
      <span className="tabular-nums">{time}</span>
      <span>|</span>
      <BracketCount count={count} t={t} />
    </div>
  );
}

function BracketCount({ count, t }: { count: number; t: any }) {
  return (
    <span className="tabular-nums">
      {t("participants")}: <span className="inline-block min-w-[3ch]">{count}</span>
    </span>
  );
}

function BracketStatus({ status, t }: { status: string; t: any }) {
  return <Badge variant={status === "started" ? "default" : "destructive"}>{t(status)}</Badge>;
}
