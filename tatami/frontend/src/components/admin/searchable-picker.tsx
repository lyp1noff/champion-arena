"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";

type SearchableOption = {
  value: string;
  label: string;
  keywords?: string;
};

interface SearchablePickerProps {
  options: SearchableOption[];
  value?: string;
  placeholder: string;
  searchPlaceholder: string;
  emptyText: string;
  onChange: (value: string) => void;
}

export function SearchablePicker({
  options,
  value,
  placeholder,
  searchPlaceholder,
  emptyText,
  onChange,
}: SearchablePickerProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selected = options.find((option) => option.value === value);
  const normalizedQuery = query.trim().toLowerCase();
  const filteredOptions = useMemo(() => {
    if (!normalizedQuery) {
      return options;
    }
    return options.filter((option) => {
      const haystack = `${option.label} ${option.keywords ?? ""}`.toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [normalizedQuery, options]);

  return (
    <div ref={rootRef} className="relative">
      <Button
        type="button"
        variant="outline"
        className="w-full justify-between overflow-hidden text-left"
        onClick={() => setOpen((current) => !current)}
      >
        <span className="truncate">{selected?.label ?? placeholder}</span>
        <span className="ml-2 text-xs text-gray-500">▼</span>
      </Button>

      {open ? (
        <div className="absolute z-20 mt-2 w-full rounded-md border bg-white shadow-lg">
          <div className="border-b p-2">
            <input
              autoFocus
              className="h-9 w-full rounded-md border px-3 text-sm outline-none"
              placeholder={searchPlaceholder}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
          <div className="max-h-64 overflow-y-auto p-1">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-6 text-center text-sm text-gray-500">{emptyText}</div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className="block w-full rounded-sm px-3 py-2 text-left text-sm hover:bg-gray-100"
                  onClick={() => {
                    onChange(option.value);
                    setOpen(false);
                    setQuery("");
                  }}
                >
                  {option.label}
                </button>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
