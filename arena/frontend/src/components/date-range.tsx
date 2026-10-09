"use client";

interface DateRangeProps {
  start: string | Date;
  end: string | Date;
  locale: string;
}

export function DateRange({ start, end, locale }: DateRangeProps) {
  const startDate = new Date(start);
  const endDate = new Date(end);

  const opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "long", year: "numeric" };

  const fmt = new Intl.DateTimeFormat(locale, opts);
  const value = fmt.formatRange(startDate, endDate).replace(/[\u00a0\u202f]/g, " ");
  return <>{value}</>;
}
