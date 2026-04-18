import React from "react";

import { cn } from "@/lib/utils";

export const LivePing = ({ size = 8 }: { size?: number }) => (
  <span className="relative flex ml-0.5" style={{ width: size / 4, height: size / 4, minWidth: 6, minHeight: 6 }}>
    <span className="animate-ping absolute inline-flex w-full h-full rounded-full bg-green-500 opacity-75"></span>
    <span className="relative inline-flex w-full h-full rounded-full bg-green-600"></span>
  </span>
);

interface LiveBadgeProps {
  className?: string;
  variant?: "rounded" | "rounded-t";
  size?: "sm" | "md";
  showText?: boolean;
  style?: React.CSSProperties;
}

export const LiveBadge: React.FC<LiveBadgeProps> = ({
  className,
  variant = "rounded",
  size = "sm",
  showText = true,
  style,
}) => {
  const sizeClasses = size === "md" ? "px-2 py-1 text-sm" : "pl-1 pr-2 pt-0.5 text-xs";
  const shapeClasses = variant === "rounded-t" ? "rounded-t-lg" : "rounded-xl";

  return (
    <div
      className={cn(
        "flex items-center gap-1 font-bold dark:bg-secondary bg-stone-300",
        sizeClasses,
        shapeClasses,
        className,
      )}
      style={style}
    >
      <LivePing />
      {showText && "Live"}
    </div>
  );
};
