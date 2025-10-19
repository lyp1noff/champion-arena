"use client";

interface DateRangeProps {
  start: string | Date;
  end: string | Date;
}

export function DateRange({ start, end }: DateRangeProps) {
  const startDate = new Date(start);
  const endDate = new Date(end);

  if (
    startDate.getDate() === endDate.getDate() &&
    startDate.getMonth() === endDate.getMonth() &&
    startDate.getFullYear() === endDate.getFullYear()
  ) {
    return <>{startDate.toLocaleDateString(undefined, { day: "numeric", month: "long" })}</>;
  }

  if (startDate.getMonth() === endDate.getMonth() && startDate.getFullYear() === endDate.getFullYear()) {
    return (
      <>
        {startDate.toLocaleDateString(undefined, { day: "numeric" })}–
        {endDate.toLocaleDateString(undefined, { day: "numeric", month: "long" })}
      </>
    );
  }

  return (
    <>
      {startDate.toLocaleDateString(undefined, { day: "numeric", month: "long" })} –{" "}
      {endDate.toLocaleDateString(undefined, { day: "numeric", month: "long" })}
    </>
  );
}
