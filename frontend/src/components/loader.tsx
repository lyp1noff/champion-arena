"use client";

import { cn } from "@/lib/utils";

interface ScreenLoaderProps {
  fullscreen?: boolean;
}

export default function ScreenLoader({ fullscreen = false }: ScreenLoaderProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-center z-50 transition-opacity duration-300",
        fullscreen ? "fixed inset-0 backdrop-blur-lg bg-black/10" : "absolute inset-0"
      )}
    >
      <div className="w-16 h-16 border-4 border-gray-300 border-t-gray-600 rounded-full animate-spin"></div>
    </div>
  );
}
