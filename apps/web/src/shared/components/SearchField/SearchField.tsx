"use client";

import { Search, X } from "lucide-react";
import { useEffect, useState } from "react";

/** How long typing pauses before the search runs, so each key does not reload the list. */
const PAUSE_MS = 300;

type SearchFieldProps = {
  label: string;
  placeholder: string;
  /** The search in force, such as the one in the address. */
  value: string;
  onSearch: (value: string) => void;
  maxLength?: number;
  disabled?: boolean;
};

/** A search box that reports what was typed once typing pauses, with a button to clear it. */
export function SearchField({
  label,
  placeholder,
  value,
  onSearch,
  maxLength,
  disabled,
}: SearchFieldProps) {
  const [text, setText] = useState(value);
  // When the search changes from outside, such as Clear filters, show that instead.
  const [shown, setShown] = useState(value);
  if (value !== shown) {
    setShown(value);
    setText(value);
  }

  useEffect(() => {
    if (text.trim() === value.trim()) return;
    const timer = setTimeout(() => onSearch(text.trim()), PAUSE_MS);
    return () => clearTimeout(timer);
  }, [text, value, onSearch]);

  return (
    <div className="relative flex items-center">
      <Search
        aria-hidden="true"
        className="pointer-events-none absolute left-4 size-icon text-muted-foreground"
      />
      <input
        type="search"
        aria-label={label}
        placeholder={placeholder}
        value={text}
        maxLength={maxLength}
        disabled={disabled}
        onChange={(event) => setText(event.target.value)}
        className="h-tap w-full rounded-full border border-input bg-background pr-12 pl-11 text-body transition-colors placeholder:text-muted-foreground focus-visible:border-foreground disabled:opacity-50 [&::-webkit-search-cancel-button]:hidden"
      />
      {text && (
        <button
          type="button"
          aria-label="Clear the search"
          onClick={() => {
            setText("");
            onSearch("");
          }}
          className="absolute right-0 flex size-tap items-center justify-center rounded-full text-muted-foreground hover:text-foreground"
        >
          <X aria-hidden="true" className="size-4" />
        </button>
      )}
    </div>
  );
}
