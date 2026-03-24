"use client";

import { useState, useCallback, type FormEvent } from "react";
import { useRouter } from "next/navigation";

interface SearchInputProps {
  defaultValue?: string;
  autoFocus?: boolean;
  size?: "sm" | "lg";
}

export function SearchInput({ defaultValue = "", autoFocus = false, size = "sm" }: SearchInputProps) {
  const [query, setQuery] = useState(defaultValue);
  const router = useRouter();

  const handleSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      if (query.trim()) {
        router.push(`/search?q=${encodeURIComponent(query.trim())}`);
      }
    },
    [query, router],
  );

  return (
    <form onSubmit={handleSubmit} className="relative w-full">
      <div className="relative">
        <svg
          className={`absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] ${
            size === "lg" ? "w-5 h-5" : "w-4 h-4"
          }`}
          viewBox="0 0 16 16"
          fill="none"
        >
          <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5" />
          <path d="M11 11L14.5 14.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search videos, creators, topics..."
          autoFocus={autoFocus}
          className={`w-full bg-[var(--bg-card)] border border-[var(--border-default)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] rounded-lg outline-none transition-all focus:border-[var(--accent)]/50 focus:ring-1 focus:ring-[var(--accent)]/20 ${
            size === "lg"
              ? "pl-11 pr-4 py-3 text-base"
              : "pl-9 pr-3 py-2 text-sm"
          }`}
        />
      </div>
    </form>
  );
}
