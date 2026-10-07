"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";

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
  const [highlightedIndex, setHighlightedIndex] = useState(0);
  const [placement, setPlacement] = useState<"top" | "bottom">("bottom");
  const rootRef = useRef<HTMLDivElement | null>(null);
  const listboxId = useId();

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

  useEffect(() => {
    setHighlightedIndex(0);
  }, [normalizedQuery]);

  const choose = (nextValue: string) => {
    onChange(nextValue);
    setOpen(false);
    setQuery("");
  };

  const toggle = () => {
    if (!open && rootRef.current) {
      const bounds = rootRef.current.getBoundingClientRect();
      const spaceAbove = bounds.top;
      const spaceBelow = window.innerHeight - bounds.bottom;
      setPlacement(spaceBelow < 380 && spaceAbove > spaceBelow ? "top" : "bottom");
    }
    setOpen((current) => !current);
  };

  return (
    <div ref={rootRef} className="searchable-picker">
      <Button
        type="button"
        variant="outline"
        className="searchable-picker__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listboxId}
        onClick={toggle}
      >
        <span className="searchable-picker__value" title={selected?.label}>
          {selected?.label ?? placeholder}
        </span>
        <span className="searchable-picker__chevron" aria-hidden="true">⌄</span>
      </Button>

      {open ? (
        <div className={`searchable-picker__menu is-${placement}`}>
          <div className="searchable-picker__search-wrap">
            <input
              autoFocus
              className="searchable-picker__search"
              placeholder={searchPlaceholder}
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Escape") {
                  setOpen(false);
                } else if (event.key === "ArrowDown") {
                  event.preventDefault();
                  setHighlightedIndex((current) => Math.min(current + 1, Math.max(0, filteredOptions.length - 1)));
                } else if (event.key === "ArrowUp") {
                  event.preventDefault();
                  setHighlightedIndex((current) => Math.max(current - 1, 0));
                } else if (event.key === "Enter" && filteredOptions[highlightedIndex]) {
                  event.preventDefault();
                  choose(filteredOptions[highlightedIndex].value);
                }
              }}
            />
          </div>
          <div id={listboxId} className="searchable-picker__options" role="listbox">
            {filteredOptions.length === 0 ? (
              <div className="searchable-picker__empty">{emptyText}</div>
            ) : (
              filteredOptions.map((option, index) => (
                <button
                  key={option.value}
                  type="button"
                  className={`searchable-picker__option ${index === highlightedIndex ? "is-highlighted" : ""}`}
                  role="option"
                  aria-selected={option.value === value}
                  title={option.label}
                  onMouseEnter={() => setHighlightedIndex(index)}
                  onClick={() => choose(option.value)}
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
