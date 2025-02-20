"use client";

export default function ScreenLoader() {
  return (
    <div className="absolute inset-0 flex items-center justify-center backdrop-blur-lg z-10">
      <div className="w-16 h-16 border-4 border-gray-300 border-t-gray-600 rounded-full animate-spin"></div>
    </div>
  );
}
