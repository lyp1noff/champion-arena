"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";

const VARIANTS = {
  /** Outline + light tint over the element (match cards, table cells). */
  box: "z-[5] bg-championYellow/30 ring-2 ring-inset ring-championYellow dark:bg-championYellow/15",
  /** Tint only, drawn behind the content like a highlighter. Parent needs `relative isolate`. */
  fill: "-z-10 bg-championYellow/40 dark:bg-championYellow/20",
} as const;

/**
 * Overlay that briefly highlights its parent whenever `signature` changes after mount.
 * Remounting by key restarts the CSS animation; no timers or effects involved.
 * The parent must be positioned (relative/absolute).
 */
export function ChangeFlash({
  signature,
  className,
  variant = "box",
}: {
  signature: string;
  className?: string;
  variant?: keyof typeof VARIANTS;
}) {
  const [initial] = useState(signature);
  if (signature === initial) return null;
  return (
    <span
      key={signature}
      aria-hidden
      className={cn(
        "pointer-events-none absolute inset-0 animate-change-flash motion-reduce:hidden",
        VARIANTS[variant],
        className,
      )}
    />
  );
}
