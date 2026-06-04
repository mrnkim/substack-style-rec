"use client";

import { ReactNode } from "react";

// ─── Tooltip copy ─────────────────────────────────────────────────────────────

const TIPS: Record<string, string> = {
  "Next.js":
    "React framework powering the video discovery UI, with server-side rendering and API routes.",
  "client library":
    "Fetch helpers that call the FastAPI backend for videos, recommendations, and search.",
  FastAPI:
    "Python web server exposing REST endpoints. Route handlers call Pixeltable directly to store, transform, and query multimodal data.",
  pixeltable:
    "Declarative multimodal backend with tables, computed columns, embedding indexes, and similarity search built in.",
  store:
    "Insert videos and creators as rows. Media files and structured data live together in one table.",
  transform:
    "Computed columns that run UDFs and call external APIs automatically on insert.",
  query:
    "Similarity search via .similarity() and filtering. Uses pgvector under the hood.",
  "Twelve Labs":
    "Multimodal video understanding API. Pixeltable's Twelve Labs integration handles auth, batching, retries, and stores vectors as computed columns automatically.",
  embed:
    "Embed API v2 with Marengo 3.0. Returns 512-dim vectors that capture the visual content of each scene.",
  analyze:
    "Analyze API extracting structured attributes: topic, style, and tone from video content.",
};

// ─── Inline SVG icons ─────────────────────────────────────────────────────────

type IconProps = { className?: string };

function MonitorIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <rect width="20" height="14" x="2" y="3" rx="2" />
      <line x1="8" x2="16" y1="21" y2="21" />
      <line x1="12" x2="12" y1="17" y2="21" />
    </svg>
  );
}

function ServerIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <rect width="20" height="8" x="2" y="2" rx="2" />
      <rect width="20" height="8" x="2" y="14" rx="2" />
      <line x1="6" x2="6.01" y1="6" y2="6" />
      <line x1="6" x2="6.01" y1="18" y2="18" />
    </svg>
  );
}

function DatabaseIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5V19A9 3 0 0 0 21 19V5" />
      <path d="M3 12A9 3 0 0 0 21 12" />
    </svg>
  );
}

function CpuIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <rect width="16" height="16" x="4" y="4" rx="2" />
      <rect width="6" height="6" x="9" y="9" rx="1" />
      <path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2" />
    </svg>
  );
}

function SearchIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <circle cx="11" cy="11" r="8" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  );
}

function WorkflowIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <rect width="8" height="8" x="3" y="3" rx="2" />
      <path d="M7 11v4a2 2 0 0 0 2 2h4" />
      <rect width="8" height="8" x="13" y="13" rx="2" />
    </svg>
  );
}

function ZapIcon({ className }: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z" />
    </svg>
  );
}

// ─── Hover popover (CSS-only) ─────────────────────────────────────────────────

function Hover({
  tip,
  children,
}: {
  tip?: string;
  children: ReactNode;
}) {
  if (!tip) return <>{children}</>;
  return (
    <div className="group/tip relative">
      {children}
      <span
        role="tooltip"
        className="pointer-events-none absolute left-1/2 top-[calc(100%+8px)] z-50 w-[240px] -translate-x-1/2 rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--bg-elevated)] px-3 py-2 text-[11px] font-normal leading-snug text-[var(--text-secondary)] opacity-0 shadow-[var(--shadow-elevated)] transition-opacity duration-150 group-hover/tip:opacity-100 group-focus-within/tip:opacity-100"
      >
        {tip}
      </span>
    </div>
  );
}

// ─── Diagram primitives ───────────────────────────────────────────────────────

function DiagNode({
  label,
  sub,
  icon: Icon,
  tip,
  children,
}: {
  label: string;
  sub?: string;
  icon?: (props: IconProps) => ReactNode;
  tip?: string;
  children?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-card)] p-3 text-center shadow-[var(--shadow-card)] transition-colors hover:border-[var(--border-accent)]">
      <Hover tip={tip}>
        <div className="mb-0.5 flex items-center justify-center gap-1.5">
          {Icon && <Icon className="w-3.5 h-3.5 text-[var(--text-secondary)]" />}
          <span className="text-xs font-semibold text-[var(--text-primary)]">
            {label}
          </span>
        </div>
        {sub && (
          <span className="block max-w-[200px] text-[11px] leading-snug text-[var(--text-tertiary)]">
            {sub}
          </span>
        )}
      </Hover>
      {children && <div className="mt-2 w-full">{children}</div>}
    </div>
  );
}

function Pill({ label }: { label: string }) {
  const tip = TIPS[label];
  const pill = (
    <span className="inline-block rounded-md border border-[var(--border-default)] bg-[var(--bg-elevated)] px-2.5 py-1 text-[11px] font-medium text-[var(--text-primary)] shadow-[var(--shadow-card)]">
      {label}
    </span>
  );
  return <Hover tip={tip}>{pill}</Hover>;
}

function Zone({
  title,
  className,
  children,
}: {
  title: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={`flex flex-col gap-3 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--bg-surface)]/40 p-4 ${className ?? ""}`}
    >
      <div className="text-center text-[9px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
        {title}
      </div>
      {children}
    </div>
  );
}

function IntegrationBadge({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-center">
      <span className="inline-flex items-center gap-1 rounded-full border border-[var(--border-accent)] bg-[var(--accent-muted)] px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-[var(--accent)]">
        <ZapIcon className="w-2.5 h-2.5" />
        {text}
      </span>
    </div>
  );
}

function PixeltableBox({ children }: { children: ReactNode }) {
  return (
    <div
      className="w-full rounded-[var(--radius-lg)] border border-[var(--border-accent)] p-4 shadow-[var(--shadow-card)]"
      style={{
        background:
          "linear-gradient(to bottom, var(--accent-muted), transparent)",
      }}
    >
      {children}
    </div>
  );
}

function FlowArrow({ label }: { label: string }) {
  return (
    <div className="flex shrink-0 items-center justify-center gap-2 py-1 md:flex-col md:gap-1 md:px-2 md:py-0">
      <svg
        width="48"
        height="20"
        viewBox="0 0 48 20"
        fill="none"
        className="rotate-90 text-[var(--text-tertiary)] md:rotate-0"
        aria-hidden
      >
        <path d="M4 10H40" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        <path d="M36 5L42 10L36 15" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="whitespace-nowrap text-[9px] font-medium text-[var(--text-tertiary)]">
        {label}
      </span>
    </div>
  );
}

function BiFlowArrow() {
  return (
    <div className="flex shrink-0 flex-col items-center justify-center gap-1 px-2 py-1 md:gap-0.5 md:py-0">
      <span className="whitespace-nowrap text-[9px] font-medium text-[var(--text-tertiary)]">
        videos
      </span>
      <svg
        width="48"
        height="14"
        viewBox="0 0 48 14"
        fill="none"
        className="rotate-90 text-[var(--accent)] md:rotate-0"
        aria-hidden
      >
        <path d="M4 7H40" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="4 3" />
        <path d="M36 3L42 7L36 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <svg
        width="48"
        height="14"
        viewBox="0 0 48 14"
        fill="none"
        className="rotate-90 text-[var(--accent)] md:rotate-0"
        aria-hidden
      >
        <path d="M8 7H44" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeDasharray="4 3" />
        <path d="M12 3L6 7L12 11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span className="whitespace-nowrap text-[9px] font-medium text-[var(--text-tertiary)]">
        vectors
      </span>
    </div>
  );
}

// ─── Main diagram ─────────────────────────────────────────────────────────────

export default function ArchitectureDiagram() {
  return (
    <div className="w-full">
      <div className="p-2">
        <div className="flex flex-col items-stretch gap-2 md:flex-row md:gap-0">
          {/* LEFT: the app */}
          <Zone title="the app" className="flex-1">
            <DiagNode
              label="Next.js"
              sub="frontend"
              icon={MonitorIcon}
              tip={TIPS["Next.js"]}
            >
              <div className="mt-1 flex items-center justify-center gap-1.5">
                <Pill label="client library" />
              </div>
            </DiagNode>
          </Zone>

          <FlowArrow label="HTTP" />

          {/* CENTER: server-side */}
          <Zone title="server-side" className="flex-[1.8]">
            <DiagNode
              label="FastAPI"
              sub="web server"
              icon={ServerIcon}
              tip={TIPS["FastAPI"]}
            />

            <IntegrationBadge text="pixeltable integration" />

            <PixeltableBox>
              <Hover tip={TIPS.pixeltable}>
                <div className="mb-3 flex items-center justify-center gap-1.5">
                  <ZapIcon className="w-3.5 h-3.5 text-[var(--accent)]" />
                  <span className="text-xs font-semibold text-[var(--text-primary)]">
                    pixeltable
                  </span>
                  <span className="ml-1 text-[10px] text-[var(--text-tertiary)]">
                    multimodal backend
                  </span>
                </div>
              </Hover>

              <div className="grid grid-cols-3 gap-2">
                <Hover tip={TIPS.store}>
                  <div className="flex flex-col items-center justify-center rounded-md border border-[var(--border-default)] bg-[var(--bg-card)] p-2.5 text-center">
                    <DatabaseIcon className="mb-1 w-3.5 h-3.5 text-[var(--text-secondary)]" />
                    <span className="text-[11px] font-semibold text-[var(--text-primary)]">
                      store
                    </span>
                    <span className="mt-0.5 text-[10px] leading-snug text-[var(--text-tertiary)]">
                      tables &amp; views
                    </span>
                  </div>
                </Hover>
                <Hover tip={TIPS.transform}>
                  <div className="flex flex-col items-center justify-center rounded-md border border-[var(--border-default)] bg-[var(--bg-card)] p-2.5 text-center">
                    <CpuIcon className="mb-1 w-3.5 h-3.5 text-[var(--text-secondary)]" />
                    <span className="text-[11px] font-semibold text-[var(--text-primary)]">
                      transform
                    </span>
                    <span className="mt-0.5 text-[10px] leading-snug text-[var(--text-tertiary)]">
                      UDFs · built-ins · AI integrations
                    </span>
                  </div>
                </Hover>
                <Hover tip={TIPS.query}>
                  <div className="flex flex-col items-center justify-center rounded-md border border-[var(--border-default)] bg-[var(--bg-card)] p-2.5 text-center">
                    <SearchIcon className="mb-1 w-3.5 h-3.5 text-[var(--text-secondary)]" />
                    <span className="text-[11px] font-semibold text-[var(--text-primary)]">
                      query
                    </span>
                    <span className="mt-0.5 text-[10px] leading-snug text-[var(--text-tertiary)]">
                      embedding indexes · .similarity()
                    </span>
                  </div>
                </Hover>
              </div>
            </PixeltableBox>
          </Zone>

          <BiFlowArrow />

          {/* RIGHT: external */}
          <Zone title="external" className="flex-1">
            <DiagNode
              label="Twelve Labs"
              sub="video embeddings"
              icon={WorkflowIcon}
              tip={TIPS["Twelve Labs"]}
            >
              <div className="mt-1 flex items-center justify-center gap-1.5">
                <Pill label="embed" />
                <Pill label="analyze" />
              </div>
            </DiagNode>

            <IntegrationBadge text="pixeltable integration" />

            <div className="text-center text-[10px] leading-snug text-[var(--text-tertiary)]">
              Pixeltable handles auth, batching, retries, and stores results as
              computed columns
            </div>
          </Zone>
        </div>
      </div>
    </div>
  );
}
