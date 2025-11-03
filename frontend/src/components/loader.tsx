import { cn } from "@/lib/utils";

interface ScreenLoaderProps {
  fullscreen?: boolean;
  className?: string;
}

export default function ScreenLoader({ fullscreen = false, className }: ScreenLoaderProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-center z-50 transition-opacity duration-300",
        fullscreen ? "fixed inset-0 backdrop-blur-xs bg-black/5" : "",
        className,
      )}
    >
      <div className="w-16 h-16 border-4 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
    </div>
  );
}
