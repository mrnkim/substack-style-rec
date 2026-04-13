"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function Nav() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Home" },
    { href: "/explore", label: "Explore" },
    { href: "/search", label: "Search" },
    { href: "/upload", label: "Upload" },
  ];

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-14 flex items-center px-8 bg-[var(--bg-primary)]/80 backdrop-blur-xl border-b border-[var(--border-light)]">
      {/* Logo */}
      <Link href="/" className="flex items-center gap-2 mr-10 group">
        <div className="w-7 h-7 rounded-md bg-[var(--accent)] flex items-center justify-center transition-transform group-hover:scale-110">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M3 3L8 13L13 3" stroke="#1D1C1B" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <span className="text-sm font-semibold tracking-tight text-[var(--text-primary)]">
          CuratorAI
        </span>
      </Link>

      {/* Nav links */}
      <div className="flex items-center gap-1">
        {links.map((link) => {
          const isActive = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                isActive
                  ? "text-[var(--text-primary)] bg-[var(--bg-elevated)]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-card)]"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </div>

      {/* Right side — TwelveLabs badge */}
      <div className="ml-auto flex items-center gap-3">
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-[var(--accent-muted)] border border-[var(--border-accent)]">
          <div className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" />
          <span className="text-xs font-medium text-[var(--accent)]">Powered by TwelveLabs + Pixeltable</span>
        </div>
      </div>
    </nav>
  );
}
