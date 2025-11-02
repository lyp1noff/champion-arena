"use client";

interface DateRangeProps {
  start: string | Date;
  end: string | Date;
  locale: string;
}

export function DateRange({ start, end, locale }: DateRangeProps) {
  const startDate = new Date(start);
  const endDate = new Date(end);

  const sameYear = startDate.getFullYear() === endDate.getFullYear();
  const opts: Intl.DateTimeFormatOptions = sameYear
    ? { day: "numeric", month: "long" }
    : { day: "numeric", month: "long", year: "numeric" };

  const fmt = new Intl.DateTimeFormat(locale, opts);
  return <>{fmt.formatRange(startDate, endDate)}</>;
}
